#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""链式生成守护进程：独立于 Web 控制台运行，持续推进链条。

用法（后台运行，关掉终端也不停）：
    nohup python3 chain_daemon.py > chain_daemon.log 2>&1 &

逻辑（v0.13.32 多 GPU 实例版）：每 20 秒把活动任务按归属 server 分组，
对每个实例分别调用 get_status（内部含 advance_chain 自动推进）；
上一段完成即自动抽帧上传、提交下一段到**同实例**，直到所有任务结束。
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batch_console as bc


def _active_server_groups(state):
    """活动任务（有 prompt_id 未结束 / chain_waiting）按归属实例分组。
    返回 {server: [task,...]}；waiting 任务沿链上溯归属，与 get_status/
    advance_chain 内部路由一致，保证同链任务在同一组。"""
    tasks = state.get("tasks", [])
    dft = state.get("server") or bc.DEFAULT_SERVER
    groups = {}
    for t in tasks:
        pid = t.get("prompt_id")
        waiting = bool(t.get("chain_waiting")) and not pid
        active = waiting or (pid and not t.get("chain_done") and not t.get("error")
                             and not t.get("downloaded"))
        if not active:
            continue
        srv = bc._task_server_of(t, tasks, dft)
        groups.setdefault(srv, []).append(t)
    return groups


def main():
    print(f"[daemon] 启动（多实例分组模式），默认服务器 {bc.DEFAULT_SERVER}，"
          f"注册实例 {[s['url'] for s in bc._server_list()]}，每 20 秒检查一次", flush=True)
    # 一次性迁移：旧任务补 server 字段（按 /history 真实落点回填）
    try:
        st = bc.load_state()
        if bc._migrate_tasks_servers(st):
            bc.save_state(st)
            print("[daemon] 旧任务已按 /history 回填归属实例", flush=True)
    except Exception as e:
        print(f"[daemon] 任务实例迁移异常（不影响运行）：{e}", flush=True)
    while True:
        try:
            state = bc.load_state()
            groups = _active_server_groups(state)
            if not groups:
                print(f"[daemon] {time.strftime('%H:%M:%S')} 无活动任务，持续待命", flush=True)
                time.sleep(20)
                continue
            for server in sorted(groups):
                n_pending = len(groups[server])
                result = bc.get_status(server)
                if not result.get("server_ok"):
                    print(f"[daemon:{server}] 服务器异常：{result.get('error')}"
                          f"（本组 {n_pending} 个活动任务保持等待）", flush=True)
                    continue
                st = result["tasks"]
                active = [t for t in st if t["status"] in ("queued", "running", "waiting")]
                done = [t for t in st if t["status"] == "completed"]
                brief = ", ".join(
                    "{}:{}".format(t.get("name", "?"), t["status"]) for t in st[-10:]
                )
                print(
                    "[daemon:{}] {} 活动 {} 完成 {} | {}".format(
                        server.rsplit(":", 1)[-1], time.strftime("%H:%M:%S"),
                        len(active), len(done), brief
                    ),
                    flush=True,
                )
        except Exception as e:
            print(f"[daemon] 错误：{e}", flush=True)
        time.sleep(20)


if __name__ == "__main__":
    main()
