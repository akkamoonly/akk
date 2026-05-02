import pyautogui
import time
import sqlite3
from datetime import datetime
from enum import Enum


# --- 1. 定义战斗状态 ---
class GameState(Enum):
    WAITING = "WAITING"  # 等待动画/发牌
    PLAYER_TURN = "PLAYER_TURN"  # 玩家回合（决策阶段）
    ACTION_EXECUTE = "ACTION_EXECUTE"  # 执行动作（拖拽打牌等）
    END_TURN = "END_TURN"  # 结束回合


# --- 2. 自动化机器人主类 ---
class STSAutoBot:
    def __init__(self):
        self.state = GameState.WAITING
        self.current_card_to_play = None
        self.combat_active = False  # 初始状态下战斗未开始

    # ================= 基础通用工具 =================

    def log_action(self, action_name, result, error_msg=""):
        """将测试结果或动作记录写入 SQLite 数据库"""
        try:
            conn = sqlite3.connect('sts_test.db')
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO test_runs (test_case_name, result, error_msg, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (action_name, result, error_msg, timestamp))
            conn.commit()
            conn.close()
            print(f"📝 日志: [{result}] {action_name} {error_msg}")
        except Exception as db_err:
            print(f"⚠️ 写入数据库失败: {db_err}")

    def find_and_click(self, image_path):
        """在屏幕上寻找目标图片并点击"""
        print(f"正在尝试寻找并点击: {image_path} ...")
        try:
            # 使用 confidence 降低匹配精度要求
            location = pyautogui.locateOnScreen(image_path, confidence=0.8)
            if location is not None:
                center_x, center_y = pyautogui.center(location)
                pyautogui.moveTo(center_x, center_y, duration=0.2)
                pyautogui.click()
                print(f"✅ 成功点击: {image_path}")
                return True
            return False
        except pyautogui.ImageNotFoundException:
            return False
        except Exception as e:
            print(f"⚠️ 图像匹配发生异常: {e}")
            return False

    # ================= 阶段一：启动与进图 =================

    def launch_game_flow(self):
        """执行从主界面到进入地图的自动化流程"""
        print("\n--- 🚀 开始执行启动进图流程 ---")
        try:
            # 1. 点击 "Play"
            if not self.find_and_click('images/play.png'):
                raise Exception("未找到 '开始游戏' 按钮")
            time.sleep(1)

            # 2. 点击 "Standard"
            if not self.find_and_click('images/standard.png'):
                raise Exception("未找到 '标准模式' 按钮")
            time.sleep(1)

            # 3. 点击 "Ironclad"
            if not self.find_and_click('images/ironclad.png'):
                raise Exception("未找到 '铁甲战士' 头像")
            time.sleep(1)

            # 4. 点击 "Embark"
            if not self.find_and_click('images/embark.png'):
                raise Exception("未找到 '启程' 按钮")

            print("🎉 进图流程全部执行完毕！准备进入战斗状态机...")
            self.log_action("LaunchGameFlow", "PASS")
            return True

        except Exception as e:
            error_info = str(e)
            print(f"❌ 进图流程中断: {error_info}")
            self.log_action("LaunchGameFlow", "FAIL", error_msg=error_info)
            return False

    # ================= 阶段二：战斗状态机 =================

    def handle_waiting(self):
        print("⏳ [状态: WAITING] 等待敌人行动或发牌...")
        # 实际开发中这里需不断截图识别“你的回合”字样，此处用 sleep 模拟
        time.sleep(2)
        print("--> 轮到玩家行动！")
        self.state = GameState.PLAYER_TURN

    def handle_player_turn(self):
        print("🧠 [状态: PLAYER_TURN] 扫描手牌和能量...")
        # 模拟决策：假设找到了打击卡且有能量
        found_strike = True
        energy_available = True

        if found_strike and energy_available:
            self.current_card_to_play = "strike_card.png"
            print(f"--> 决策完毕，准备打出 {self.current_card_to_play}")
            self.state = GameState.ACTION_EXECUTE
        else:
            print("--> 没牌可打或能量耗尽。")
            self.state = GameState.END_TURN

    def handle_action_execute(self):
        print(f"⚔️ [状态: ACTION_EXECUTE] 正在执行动作: 打出 {self.current_card_to_play}")
        # 实际开发中这里写拖拽鼠标的代码，此处用 sleep 模拟
        time.sleep(1)
        self.log_action(f"PlayCard_{self.current_card_to_play}", "PASS")

        # 动作执行完毕，回到决策状态
        self.current_card_to_play = None
        self.state = GameState.PLAYER_TURN

    def handle_end_turn(self):
        print("🛑 [状态: END_TURN] 正在结束回合...")
        # 实际开发中这里调用 self.find_and_click('images/end_turn.png')
        time.sleep(1)
        self.log_action("EndTurn", "PASS")
        print("--> 回合结束，进入等待。")
        self.state = GameState.WAITING

        # 为了演示不陷入死循环，打完一个回合后我们结束战斗循环
        self.combat_active = False

    def run_combat_loop(self):
        """运行战斗状态机主循环"""
        print("\n--- ⚔️ 战斗状态机启动 ---")
        self.combat_active = True
        self.state = GameState.WAITING  # 重置为初始状态

        while self.combat_active:
            if self.state == GameState.WAITING:
                self.handle_waiting()
            elif self.state == GameState.PLAYER_TURN:
                self.handle_player_turn()
            elif self.state == GameState.ACTION_EXECUTE:
                self.handle_action_execute()
            elif self.state == GameState.END_TURN:
                self.handle_end_turn()

            time.sleep(0.1)  # 降低 CPU 占用

        print("🎉 战斗模块执行完毕，状态机挂起。")

    # ================= 终极启动入口 =================

    def start(self):
        print("🤖 STS AutoBot 已启动，请在 3 秒内将游戏窗口置顶...")
        time.sleep(3)

        # 第一步：尝试执行进图流程
        is_launched = self.launch_game_flow()

        # 第二步：如果进图成功，并且后续检测到了怪物（模拟），则启动状态机
        if is_launched:
            # 假设等待 3 秒进图动画并遭遇怪物
            time.sleep(3)
            self.run_combat_loop()
        else:
            print("🛑 由于进图流程失败，战斗模块取消执行。")


# --- 3. 运行脚本 ---
if __name__ == "__main__":
    bot = STSAutoBot()
    bot.start()