import random
import tkinter as tk
from tkinter import messagebox, simpledialog
from collections import defaultdict
import time
from itertools import combinations  # 添加这行导入

class BigTwoGame:
    def __init__(self, num_players, ai_players=None):
        self.num_players = num_players
        self.players = {i: [] for i in range(num_players)}
        self.current_player = 0
        self.last_played = None  # (player_id, cards, hand_type, value)
        self.consecutive_passes = 0
        self.first_turn = True
        self.finished = False
        self.winner = None
        self.first_card = None
        self.dialogues = []  # 存储游戏中的对话
        
        # 设置AI玩家
        self.ai_players = ai_players if ai_players else []
        
        # 牌型等级和比较值
        self.hand_ranks = {
            "single": 1, "pair": 2, "three": 3, 
            "straight": 4, "flush": 5, "full_house": 6,
            "four_of_a_kind": 7, "straight_flush": 8
        }
        
        # 创建并洗牌
        self.create_deck()
        self.deal_cards()
        
        # 找起始玩家（持有最小牌的玩家）
        self.find_starting_player()
    
    def create_deck(self):
        """创建一副扑克牌（52张，不含鬼牌）"""
        suits = ['♠', '♥', '♣', '♦']  # 黑桃、红心、梅花、方块
        ranks = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
        self.deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
        random.shuffle(self.deck)
        
    def deal_cards(self):
        """发牌给玩家"""
        if self.num_players == 2:
            # 两人游戏：各取13张
            for i in range(2):
                self.players[i] = self.deck[i*13:(i+1)*13]
        elif self.num_players == 3:
            # 三人游戏：各取13张，剩余13张不用
            for i in range(3):
                self.players[i] = self.deck[i*13:(i+1)*13]
        else:  # 四人游戏
            for i in range(4):
                self.players[i] = self.deck[i*13:(i+1)*13]
        
        # 按牌的大小排序
        for player in self.players:
            self.sort_cards(player)
    
    def find_starting_player(self):
        """找到拥有最小牌的玩家（方块3优先，否则找最小牌）"""
        min_card = "2♠"  # 初始化为最大的牌
        
        # 首先寻找方块3
        for player_id, cards in self.players.items():
            if "3♦" in cards:
                self.current_player = player_id
                self.first_card = "3♦"
                return
            # 同时记录最小牌
            if cards:  # 确保玩家有牌
                card_val = self.card_value(cards[0])
                if card_val < self.card_value(min_card):
                    min_card = cards[0]
                    self.current_player = player_id
        
        self.first_card = min_card
    
    def card_value(self, card):
        """获取卡牌的比较值"""
        # 提取点数和花色
        if card[-1] in ['♠', '♥', '♣', '♦']:
            rank = card[:-1]
            suit = card[-1]
        else:
            # 处理10的情况
            if len(card) == 3:
                rank = card[:2]
                suit = card[2]
            else:
                rank = card[0]
                suit = card[1]
        
        # 点数顺序：3<4<5<6<7<8<9<10<J<Q<K<A<2
        rank_values = {
            '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6, 
            '9': 7, '10': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12, '2': 13
        }
        
        # 花色顺序：黑桃 > 红心 > 梅花 > 方块
        suit_values = {'♠': 4, '♥': 3, '♣': 2, '♦': 1}
        
        return (rank_values[rank] * 10) + suit_values[suit]
    
    def sort_cards(self, player_id):
        """对玩家手牌进行排序（从小到大）"""
        self.players[player_id] = sorted(
            self.players[player_id], 
            key=lambda card: self.card_value(card)
        )
    
    def validate_hand(self, cards):
        """验证牌型并返回牌型和比较值"""
        num_cards = len(cards)
        card_values = [self.card_value(c) for c in cards]
        
        # 单张牌
        if num_cards == 1:
            return "single", card_values[0]
        
        # 对子
        if num_cards == 2:
            if card_values[0] // 10 == card_values[1] // 10:
                return "pair", max(card_values)
            return None, None
        
        # 三张
        if num_cards == 3:
            if card_values[0] // 10 == card_values[1] // 10 == card_values[2] // 10:
                return "three", card_values[0] // 10
            return None, None
        
        # 5张牌型（顺子、同花、葫芦、四带一、同花顺）
        if num_cards != 5:
            return None, None
        
        # 检查是否同花色
        suits = [card[-1] for card in cards]
        is_flush = len(set(suits)) == 1
        
        # 检查是否顺子
        ranks = sorted([cv // 10 for cv in card_values])
        is_straight = True
        for i in range(1, 5):
            if ranks[i] != ranks[i-1] + 1:
                is_straight = False
                break
        
        # 处理特殊顺子：A-2-3-4-5
        if set(ranks) == {1, 2, 3, 4, 12}:  # {3,4,5,6,12} -> 3,4,5,6,A
            is_straight = True
            ranks = [1, 2, 3, 4, 5]  # 视为最小的顺子
        
        # 同花顺
        if is_flush and is_straight:
            return "straight_flush", max(card_values)
        
        # 普通顺子
        if is_straight:
            return "straight", max(card_values)
        
        # 同花
        if is_flush:
            return "flush", max(card_values)
        
        # 检查是否为葫芦（三带二）
        rank_count = defaultdict(int)
        for cv in card_values:
            rank_count[cv // 10] += 1
        
        # 寻找三张和一对的组合
        if sorted(rank_count.values()) == [2, 3]:
            # 返回三张部分的点数
            for rank, count in rank_count.items():
                if count == 3:
                    return "full_house", rank * 10
        
        # 检查四带一
        if sorted(rank_count.values()) == [1, 4]:
            # 返回四张部分的点数
            for rank, count in rank_count.items():
                if count == 4:
                    return "four_of_a_kind", rank * 10
        
        # 无效牌型
        return None, None
    
    def can_play(self, cards):
        """检查能否出牌压制上家"""
        # 如果没有上家出牌，可以出任何牌
        if not self.last_played:
            return True
        
        # 检查牌数是否一致
        last_num_cards = len(self.last_played[1])
        current_num_cards = len(cards)
        if last_num_cards != current_num_cards:
            return False
        
        # 验证牌型
        hand_type, hand_value = self.validate_hand(cards)
        if not hand_type:
            return False
        
        last_hand_type, last_hand_value, last_rank = self.last_played[2:]
        
        # 比较牌型等级
        current_rank = self.hand_ranks[hand_type]
        last_rank = self.hand_ranks[last_hand_type]
        
        # 牌型等级更高
        if current_rank > last_rank:
            return True
        
        # 牌型等级相同，比较数值
        if current_rank == last_rank and hand_value > last_hand_value:
            return True
        
        return False
    
    def play_turn(self, cards_to_play=None):
        """执行一个回合"""
        player_id = self.current_player
        
        # 玩家选择pass
        if not cards_to_play:
            self.consecutive_passes += 1
            
            # 连续三家pass，重置出牌权
            if self.consecutive_passes >= self.num_players - 1:
                self.last_played = None
                self.consecutive_passes = 0
                # AI喝倒彩
                if player_id in self.ai_players:
                    self.dialogues.append((player_id, "看我轻松拿捏啦～"))
            
            # 转到下一玩家
            self.current_player = (player_id + 1) % self.num_players
            return True, "过牌成功"
        
        # 验证玩家出的牌是否都在手牌中
        if not all(card in self.players[player_id] for card in cards_to_play):
            return False, "您没有这些牌"
        
        # 特殊规则：首回合必须包含最小牌
        if self.first_turn:
            if self.first_card not in cards_to_play:
                return False, f"首回合必须包含最小牌: {self.first_card}"
            self.first_turn = False
        
        # 检查能否压制上家
        if not self.can_play(cards_to_play):
            return False, "牌不够大"
        
        # 验证牌型
        hand_type, hand_value = self.validate_hand(cards_to_play)
        if not hand_type:
            return False, "无效牌型"
        
        # 成功出牌
        for card in cards_to_play:
            self.players[player_id].remove(card)
        
        # 更新游戏状态
        self.last_played = (
            player_id, 
            cards_to_play, 
            hand_type, 
            hand_value, 
            self.hand_ranks[hand_type]
        )
        self.consecutive_passes = 0
        
        # 检查玩家是否获胜
        if not self.players[player_id]:
            self.finished = True
            self.winner = player_id
            if player_id in self.ai_players:
                self.dialogues.append((player_id, "弱吱吱就是弱吱吱！"))
            else:
                # 人类赢了，AI表示敬意
                for ai_id in self.ai_players:
                    self.dialogues.append((ai_id, "你真是泥猛鱼噢！"))
            return True, "出牌成功，游戏胜利!"
        
        # 转到下一玩家
        self.current_player = (player_id + 1) % self.num_players
        return True, "出牌成功"
        
    def generate_possible_plays(self, hand):
        """生成所有可能的出牌组合，并按优先级排序"""
        possible_plays = []
        
        # 生成所有可能的单张
        for card in hand:
            possible_plays.append(([card], "single", self.card_value(card)))
        
        # 生成所有可能的对子
        for i in range(len(hand)-1):
            for j in range(i+1, len(hand)):
                if hand[i][:-1] == hand[j][:-1]:
                    pair = [hand[i], hand[j]]
                    possible_plays.append((pair, "pair", self.card_value(hand[j])))
        
        # 生成所有可能的三张
        for i in range(len(hand)-2):
            for j in range(i+1, len(hand)-1):
                for k in range(j+1, len(hand)):
                    if hand[i][:-1] == hand[j][:-1] == hand[k][:-1]:
                        three = [hand[i], hand[j], hand[k]]
                        possible_plays.append((three, "three", self.card_value(hand[k])))
        
        # 生成所有可能的五张牌型
        if len(hand) >= 5:
            for combo in combinations(hand, 5):
                cards = list(combo)
                hand_type, hand_value = self.validate_hand(cards)
                if hand_type:
                    possible_plays.append((cards, hand_type, hand_value))
        
        # 按优先级排序
        def get_priority(play):
            type_priority = {
                "straight_flush": 10,
                "four_of_a_kind": 9,  # 四带一
                "full_house": 8,       # 三带二
                "flush": 7,
                "straight": 6,
                "three": 5,
                "pair": 4,
                "single": 3
            }
            return type_priority.get(play[1], 0)
        
        # 按优先级降序和牌值升序排序（优先级高的在前，同样优先级时牌值小的在前）
        possible_plays.sort(key=lambda x: (-get_priority(x), x[2]))
        
        return possible_plays
        
    def ai_play_turn(self):
        """AI玩家决策（使用优先级策略）"""
        player_id = self.current_player
        hand = self.players[player_id]
        
        # 检查是否有玩家只剩一张牌（即将获胜）
        opponent_one_card = any(
            len(self.players[pid]) == 1 
            for pid in range(self.num_players) 
            if pid != player_id and pid not in self.ai_players
        )
        
        # 如果有玩家只剩一张牌，AI表示惊讶
        if opponent_one_card:
            self.dialogues.append((player_id, "这么快就报警了？！"))
        
        # 如果AI是首回合玩家，必须包含最小牌
        if self.first_turn:
            if self.first_card not in hand:
                # 如果最小牌不在手牌中，这应该是错误情况
                return self.play_turn(None)
            
            # 尝试出单张最小牌
            if self.first_card in hand:
                return self.play_turn([self.first_card])
        
        # 如果没有上家出牌，AI获得出牌权
        if not self.last_played:
            # 生成所有可能的出牌组合并按优先级排序
            possible_plays = self.generate_possible_plays(hand)
            
            # 特殊处理：如果有对手只剩一张牌，优先出非单张牌型
            if opponent_one_card:
                # 筛选非单张牌型
                non_single_plays = [play for play in possible_plays if len(play[0]) > 1]
                
                # 如果有非单张牌型，优先选择
                if non_single_plays:
                    # 处理五张牌型的优先级关系
                    five_card_plays = [play for play in non_single_plays if len(play[0]) == 5]
                    if five_card_plays:
                        # 按优先级和牌值排序
                        five_card_plays.sort(key=lambda x: (self.hand_ranks[x[1]], x[2]))
                        
                        # 检查牌型之间的重叠关系
                        selected_play = None
                        for i, play in enumerate(five_card_plays):
                            play_cards = set(play[0])
                            # 检查这个牌型是否会拆散更高优先级的牌型
                            conflicts = False
                            for j in range(i + 1, len(five_card_plays)):
                                higher_play_cards = set(five_card_plays[j][0])
                                if play_cards.intersection(higher_play_cards):
                                    conflicts = True
                                    break
                            
                            # 如果没有冲突，选择这个牌型
                            if not conflicts:
                                selected_play = play
                                break
                        
                        # 如果没有找到不冲突的牌型，选择优先级最高的牌型
                        if not selected_play and five_card_plays:
                            selected_play = five_card_plays[-1]  # 优先级最高的
                        
                        if selected_play:
                            return self.play_turn(selected_play[0])
                    
                    # 如果没有五张牌型或无法选择，选择优先级最高的非单张牌型
                    return self.play_turn(non_single_plays[0][0])
                
                # 如果没有非单张牌型，选择最大的单张牌
                else:
                    # 按牌值从大到小排序
                    single_plays = [play for play in possible_plays if len(play[0]) == 1]
                    single_plays.sort(key=lambda x: x[2], reverse=True)
                    if single_plays:
                        return self.play_turn(single_plays[0][0])
            
            # 正常情况：没有对手只剩一张牌
            # 处理五张牌型的优先级关系
            five_card_plays = [play for play in possible_plays if len(play[0]) == 5]
            if five_card_plays:
                # 按优先级和牌值排序
                five_card_plays.sort(key=lambda x: (self.hand_ranks[x[1]], x[2]))
                
                # 检查牌型之间的重叠关系
                selected_play = None
                for i, play in enumerate(five_card_plays):
                    play_cards = set(play[0])
                    # 检查这个牌型是否会拆散更高优先级的牌型
                    conflicts = False
                    for j in range(i + 1, len(five_card_plays)):
                        higher_play_cards = set(five_card_plays[j][0])
                        if play_cards.intersection(higher_play_cards):
                            conflicts = True
                            break
                    
                    # 如果没有冲突，选择这个牌型
                    if not conflicts:
                        selected_play = play
                        break
                
                # 如果没有找到不冲突的牌型，选择优先级最高的牌型
                if not selected_play and five_card_plays:
                    selected_play = five_card_plays[-1]  # 优先级最高的
                
                if selected_play:
                    return self.play_turn(selected_play[0])
            
            # 如果没有五张牌型或无法选择，选择优先级最高的牌型
            if possible_plays:
                return self.play_turn(possible_plays[0][0])
            
            # 没有可出的牌，选择过牌
            return self.play_turn(None)
        
        # 有上家出牌，需要压制
        last_num_cards = len(self.last_played[1])
        last_hand_type = self.last_played[2]
        last_hand_value = self.last_played[3]
        
        # 生成所有可能的出牌组合并按优先级排序
        possible_plays = self.generate_possible_plays(hand)
        
        # 筛选出与上家牌数相同的组合
        same_num_plays = [play for play in possible_plays if len(play[0]) == last_num_cards]
        
        # 筛选出能压制上家的组合
        valid_plays = []
        for play in same_num_plays:
            cards, hand_type, hand_value = play
            # 检查牌型等级
            current_rank = self.hand_ranks[hand_type]
            last_rank = self.hand_ranks[last_hand_type]
            
            # 牌型等级更高
            if current_rank > last_rank:
                valid_plays.append(play)
            # 牌型等级相同，比较数值
            elif current_rank == last_rank and hand_value > last_hand_value:
                valid_plays.append(play)
        
        # 特殊处理：如果有对手只剩一张牌，优先出非单张牌型
        if opponent_one_card and valid_plays:
            # 筛选非单张牌型
            non_single_plays = [play for play in valid_plays if len(play[0]) > 1]
            
            # 如果有非单张牌型，优先选择
            if non_single_plays:
                # 处理五张牌型的优先级关系
                five_card_plays = [play for play in non_single_plays if len(play[0]) == 5]
                if five_card_plays:
                    # 按优先级和牌值排序
                    five_card_plays.sort(key=lambda x: (self.hand_ranks[x[1]], x[2]))
                    
                    # 检查牌型之间的重叠关系
                    selected_play = None
                    for i, play in enumerate(five_card_plays):
                        play_cards = set(play[0])
                        # 检查这个牌型是否会拆散更高优先级的牌型
                        conflicts = False
                        for j in range(i + 1, len(five_card_plays)):
                            higher_play_cards = set(five_card_plays[j][0])
                            if play_cards.intersection(higher_play_cards):
                                conflicts = True
                                break
                        
                        # 如果没有冲突，选择这个牌型
                        if not conflicts:
                            selected_play = play
                            break
                    
                    # 如果没有找到不冲突的牌型，选择优先级最高的牌型
                    if not selected_play and five_card_plays:
                        selected_play = five_card_plays[-1]  # 优先级最高的
                    
                    if selected_play:
                        return self.play_turn(selected_play[0])
                
                # 如果没有五张牌型或无法选择，选择优先级最高的非单张牌型
                return self.play_turn(non_single_plays[0][0])
            
            # 如果没有非单张牌型，选择最大的单张牌
            else:
                # 按牌值从大到小排序
                single_plays = [play for play in valid_plays if len(play[0]) == 1]
                single_plays.sort(key=lambda x: x[2], reverse=True)
                if single_plays:
                    return self.play_turn(single_plays[0][0])
        
        # 正常情况：没有对手只剩一张牌
        # 特殊处理五张牌型
        five_card_plays = [play for play in valid_plays if len(play[0]) == 5]
        if five_card_plays:
            # 按优先级和牌值排序
            five_card_plays.sort(key=lambda x: (self.hand_ranks[x[1]], x[2]))
            
            # 检查牌型之间的重叠关系
            selected_play = None
            for i, play in enumerate(five_card_plays):
                play_cards = set(play[0])
                # 检查这个牌型是否会拆散更高优先级的牌型
                conflicts = False
                for j in range(i + 1, len(five_card_plays)):
                    higher_play_cards = set(five_card_plays[j][0])
                    if play_cards.intersection(higher_play_cards):
                        conflicts = True
                        break
                
                # 如果没有冲突，选择这个牌型
                if not conflicts:
                    selected_play = play
                    break
            
            # 如果没有找到不冲突的牌型，选择优先级最高的牌型
            if not selected_play and five_card_plays:
                selected_play = five_card_plays[-1]  # 优先级最高的
            
            if selected_play:
                return self.play_turn(selected_play[0])
        
        # 如果有可出的牌，选择优先级最高的
        if valid_plays:
            # AI占上风时喝倒彩
            if self.consecutive_passes > 0:
                self.dialogues.append((player_id, "说你弱你就弱啦！"))
            return self.play_turn(valid_plays[0][0])
        
        # 无法压制，选择过牌
        # AI占下风时说敬仰的话
        self.dialogues.append((player_id, "哇，你怎么这么猛！"))
        return self.play_turn(None)

    def get_game_state(self, player_id):
        """获取游戏状态（用于显示）"""
        state = {
            "current_player": self.current_player,
            "last_played": self.last_played[1] if self.last_played else None,
            "last_hand_type": self.last_played[2] if self.last_played else None,
            "consecutive_passes": self.consecutive_passes,
            "finished": self.finished,
            "winner": self.winner,
            "first_turn": self.first_turn,
            "first_card": self.first_card,
            "dialogues": self.dialogues.copy()  # 复制对话列表
        }
        
        # 添加玩家手牌数量信息
        for pid in range(self.num_players):
            state_key = f"player_{pid}_cards_count"
            state[state_key] = len(self.players[pid])
        
        # 添加当前玩家的详细手牌信息
        if player_id in self.players:
            state["current_player_hand"] = self.players[player_id]
        else:
            state["current_player_hand"] = []
        
        return state


class BigTwoGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("锄大地")
        self.root.geometry("1000x700")
        self.root.configure(bg="#2E8B57")  # 海绿色背景
        
        # 创建菜单
        self.create_menu()
        
        # 游戏状态变量
        self.game = None
        self.selected_cards = []
        self.ai_thinking = False
        
        # 创建游戏界面
        self.create_welcome_screen()
        
        self.root.mainloop()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 游戏菜单
        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="新游戏", command=self.start_new_game)
        game_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="游戏", menu=game_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="游戏规则", command=self.show_rules)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_welcome_screen(self):
        """创建欢迎界面"""
        self.clear_frame()
        
        # 欢迎标题
        title_label = tk.Label(
            self.root, 
            text="锄大地", 
            font=("Arial", 50, "bold"),
            bg="#2E8B57",
            fg="white"
        )
        title_label.pack(pady=50)
        
        # 游戏规则按钮
        rules_btn = tk.Button(
            self.root,
            text="游戏规则",
            font=("Arial", 14),
            command=self.show_rules,
            bg="#3CB371",
            fg="white",
            width=15,
            height=2
        )
        rules_btn.pack(pady=10)
        
        # 开始游戏按钮
        start_btn = tk.Button(
            self.root,
            text="开始游戏",
            font=("Arial", 14),
            command=self.start_new_game,
            bg="#3CB371",
            fg="white",
            width=15,
            height=2
        )
        start_btn.pack(pady=10)
        
        # 退出按钮
        exit_btn = tk.Button(
            self.root,
            text="退出游戏",
            font=("Arial", 14),
            command=self.root.quit,
            bg="#CD5C5C",
            fg="white",
            width=15,
            height=2
        )
        exit_btn.pack(pady=10)
    
    def show_rules(self):
        """显示游戏规则"""
        rules = """
        锄大地游戏规则:
        
        1. 牌大小顺序: 2 > A > K > Q > J > 10 > ... > 3
        2. 花色大小: 黑桃(♠) > 红心(♥) > 梅花(♣) > 方块(♦)
        3. 特殊规则: 顺子 < 同花 < 葫芦 < 四带一 < 同花顺
        4. 出牌数必须与上家相同（首回合例外）
        5. 首回合必须包含最小牌(方块3或最小牌)
        6. 牌型: 单张、对子、三条、顺子、同花、葫芦、四带一、同花顺
        7. '过牌'表示跳过本轮
        
        游戏目标: 第一个出完所有手牌的玩家获胜!
        """
        messagebox.showinfo("游戏规则", rules)
    
    def start_new_game(self):
        """开始新游戏"""
        # 获取玩家数量
        num_players = simpledialog.askinteger(
            "玩家数量", 
            "请输入玩家数量 (2, 3, 4):", 
            minvalue=2, 
            maxvalue=4
        )
        
        if not num_players:
            return
        
        # 设置AI玩家
        ai_players = []
        if num_players == 2:
            # 询问是否添加AI对手
            add_ai = messagebox.askyesno("AI对手", "是否添加AI对手?")
            if add_ai:
                ai_players = [1]  # 玩家1为AI
        
        self.game = BigTwoGame(num_players, ai_players)
        self.create_game_interface()
        
        # 如果当前玩家是AI，自动进行回合
        if self.game.current_player in self.game.ai_players:
            self.ai_play()
    
    def clear_frame(self):
        """清除当前界面"""
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()
    
    def create_game_interface(self):
        """创建游戏界面"""
        self.clear_frame()
        
        # 创建顶部状态栏
        self.create_status_bar()
        
        # 创建对手手牌区域
        self.create_opponents_area()
        
        # 创建当前玩家手牌区域
        self.create_player_hand_area()
        
        # 创建操作按钮区域
        self.create_action_buttons()
        
        # 创建出牌历史区域
        self.create_history_area()
        
        # 创建对话区域
        self.create_dialogue_area()
        
        # 更新界面
        self.update_interface()
    
    def create_status_bar(self):
        """创建顶部状态栏"""
        status_frame = tk.Frame(self.root, bg="#3CB371", height=50)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="游戏进行中...",
            font=("Arial", 12, "bold"),
            bg="#3CB371",
            fg="white"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.turn_label = tk.Label(
            status_frame,
            text=f"当前玩家: {self.game.current_player}",
            font=("Arial", 12),
            bg="#3CB371",
            fg="white"
        )
        self.turn_label.pack(side=tk.RIGHT, padx=10)
    
    def create_opponents_area(self):
        """创建对手手牌区域"""
        opponents_frame = tk.Frame(self.root, bg="#2E8B57")
        opponents_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建对手区域
        self.opponent_frames = []
        for i in range(1, self.game.num_players):
            frame = tk.Frame(opponents_frame, bg="#2E8B57")
            frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 显示玩家标识（如果是AI则添加AI标记）
            player_type = "AI" if i in self.game.ai_players else "玩家"
            label = tk.Label(
                frame,
                text=f"{player_type} {i}",
                font=("Arial", 10, "bold"),
                bg="#2E8B57",
                fg="white"
            )
            label.pack(anchor=tk.W)
            
            card_frame = tk.Frame(frame, bg="#2E8B57")
            card_frame.pack(fill=tk.BOTH, expand=True)
            
            self.opponent_frames.append(card_frame)
    
    def create_player_hand_area(self):
        """创建当前玩家手牌区域"""
        player_frame = tk.Frame(self.root, bg="#2E8B57", height=200)
        player_frame.pack(fill=tk.X, padx=10, pady=5)
        
        label = tk.Label(
            player_frame,
            text="你的手牌",
            font=("Arial", 10, "bold"),
            bg="#2E8B57",
            fg="white"
        )
        label.pack(anchor=tk.W)
        
        self.player_hand_frame = tk.Frame(player_frame, bg="#2E8B57")
        self.player_hand_frame.pack(fill=tk.BOTH, expand=True)
    
    def create_action_buttons(self):
        """创建操作按钮区域"""
        action_frame = tk.Frame(self.root, bg="#2E8B57")
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.play_button = tk.Button(
            action_frame,
            text="出牌",
            font=("Arial", 12),
            command=self.play_cards,
            bg="#3CB371",
            fg="white",
            width=10,
            state=tk.DISABLED
        )
        self.play_button.pack(side=tk.LEFT, padx=10)
        
        self.pass_button = tk.Button(
            action_frame,
            text="过牌",
            font=("Arial", 12),
            command=self.pass_turn,
            bg="#CD5C5C",
            fg="white",
            width=10
        )
        self.pass_button.pack(side=tk.LEFT, padx=10)
        
        self.restart_button = tk.Button(
            action_frame,
            text="重新开始",
            font=("Arial", 12),
            command=self.start_new_game,
            bg="#4682B4",
            fg="white",
            width=10
        )
        self.restart_button.pack(side=tk.RIGHT, padx=10)
    
    def create_history_area(self):
        """创建出牌历史区域"""
        history_frame = tk.Frame(self.root, bg="#2E8B57")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        label = tk.Label(
            history_frame,
            text="出牌历史",
            font=("Arial", 10, "bold"),
            bg="#2E8B57",
            fg="white"
        )
        label.pack(anchor=tk.W)
        
        self.history_text = tk.Text(
            history_frame,
            height=5,
            bg="#F0FFF0",
            fg="black",
            font=("Arial", 10)
        )
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_text.config(state=tk.DISABLED)
    
    def create_dialogue_area(self):
        """创建对话区域"""
        dialogue_frame = tk.Frame(self.root, bg="#2E8B57")
        dialogue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        label = tk.Label(
            dialogue_frame,
            text="游戏对话",
            font=("Arial", 10, "bold"),
            bg="#2E8B57",
            fg="white"
        )
        label.pack(anchor=tk.W)
        
        self.dialogue_text = tk.Text(
            dialogue_frame,
            height=3,
            bg="#FFF0F0",
            fg="black",
            font=("Arial", 10)
        )
        self.dialogue_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.dialogue_text.config(state=tk.DISABLED)
    
    def update_interface(self):
        """更新游戏界面"""
        if not self.game:
            return
        
        # 获取当前游戏状态
        state = self.game.get_game_state(self.game.current_player)
        
        # 更新状态栏
        self.turn_label.config(text=f"当前玩家: {self.game.current_player}")
        
        if self.game.finished:
            self.status_label.config(text=f"游戏结束! 玩家 {self.game.winner} 获胜!")
            self.play_button.config(state=tk.DISABLED)
            self.pass_button.config(state=tk.DISABLED)
        else:
            self.status_label.config(text="游戏进行中...")
            self.play_button.config(state=tk.NORMAL if self.selected_cards else tk.DISABLED)
            self.pass_button.config(state=tk.NORMAL)
        
        # 更新对手区域
        for i, frame in enumerate(self.opponent_frames):
            # 清除之前的卡片
            for widget in frame.winfo_children():
                widget.destroy()
            
            # 获取对手ID
            opponent_id = (self.game.current_player + i + 1) % self.game.num_players
            
            # 显示对手手牌数量
            count = state[f"player_{opponent_id}_cards_count"]
            player_type = "AI" if opponent_id in self.game.ai_players else "玩家"
            label = tk.Label(
                frame,
                text=f"{player_type} {opponent_id} - {count}张牌",
                font=("Arial", 10),
                bg="#2E8B57",
                fg="white"
            )
            label.pack(anchor=tk.W)
            
            # 显示对手手牌（背面）
            for _ in range(min(count, 10)):  # 最多显示10张牌
                card_label = tk.Label(
                    frame, 
                    text="🂠",  # 使用扑克牌背面符号
                    font=("Arial", 16),
                    bg="white",
                    fg="black",
                    width=3,
                    height=2,
                    relief=tk.RAISED,
                    borderwidth=2
                )
                card_label.pack(side=tk.LEFT, padx=2)
            
            # 如果对手只剩一张牌，添加警告
            if count == 1 and opponent_id not in self.game.ai_players:
                warning_label = tk.Label(
                    frame,
                    text="⚠️ 只剩一张牌!",
                    font=("Arial", 10, "bold"),
                    bg="#2E8B57",
                    fg="red"
                )
                warning_label.pack(side=tk.RIGHT, padx=10)
        
        # 更新当前玩家手牌
        for widget in self.player_hand_frame.winfo_children():
            widget.destroy()
        
        # 添加首回合提示
        if self.game.first_turn and self.game.current_player not in self.game.ai_players:
            tip_label = tk.Label(
                self.player_hand_frame,
                text=f"首回合必须包含最小牌: {self.game.first_card}",
                font=("Arial", 10, "bold"),
                bg="#2E8B57",
                fg="yellow"
            )
            tip_label.pack(side=tk.TOP, pady=5)
        
        # 创建卡牌按钮
        card_frame = tk.Frame(self.player_hand_frame, bg="#2E8B57")
        card_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        for card in state["current_player_hand"]:
            # 设置花色颜色
            suit_color = {
                '♠': 'black',  # 黑桃
                '♥': 'red',    # 红心
                '♣': 'black',  # 梅花
                '♦': 'red'     # 方块
            }.get(card[-1], 'black')
            
            # 创建卡牌按钮
            card_button = tk.Button(
                card_frame,
                text=card,
                font=("Arial", 10, "bold"),
                bg="white",
                fg=suit_color,
                width=4,
                height=2,
                relief=tk.RAISED if card not in self.selected_cards else tk.SUNKEN,
                borderwidth=2,
                command=lambda c=card: self.toggle_card_selection(c)
            )
            card_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 更新出牌历史
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        
        if state["last_played"]:
            player_id = self.game.last_played[0] if self.game.last_played else "?"
            player_type = "AI" if player_id in self.game.ai_players else "玩家"
            cards = ", ".join(state["last_played"])
            hand_type = state["last_hand_type"]
            self.history_text.insert(tk.END, f"{player_type} {player_id} 出牌: {cards} ({hand_type})\n")
        else:
            if state["first_turn"]:
                self.history_text.insert(tk.END, f"首回合开始! 必须包含最小牌: {self.game.first_card}\n")
            else:
                self.history_text.insert(tk.END, "获得出牌权\n")
        
        self.history_text.config(state=tk.DISABLED)
        
        # 更新对话区域
        self.dialogue_text.config(state=tk.NORMAL)
        self.dialogue_text.delete(1.0, tk.END)
        
        # 添加对话
        for player_id, message in state["dialogues"]:
            player_type = "AI" if player_id in self.game.ai_players else "玩家"
            self.dialogue_text.insert(tk.END, f"{player_type} {player_id}: {message}\n")
        
        self.dialogue_text.config(state=tk.DISABLED)
        
        # 滚动到对话底部
        self.dialogue_text.see(tk.END)
        
        # 如果游戏结束，显示获胜信息
        if self.game.finished:
            player_type = "AI" if self.game.winner in self.game.ai_players else "玩家"
            messagebox.showinfo("游戏结束", f"{player_type} {self.game.winner} 获胜!")
    
    def toggle_card_selection(self, card):
        """切换卡牌选择状态"""
        if card in self.selected_cards:
            self.selected_cards.remove(card)
        else:
            self.selected_cards.append(card)
        
        # 更新界面
        self.update_interface()
    
    def play_cards(self):
        """出牌操作"""
        if not self.selected_cards:
            messagebox.showwarning("警告", "请选择要出的牌")
            return
        
        # 首回合必须包含最小牌
        if self.game.first_turn:
            if self.game.first_card not in self.selected_cards:
                messagebox.showwarning("警告", f"首回合必须包含最小牌: {self.game.first_card}")
                return
        
        success, message = self.game.play_turn(self.selected_cards)
        if success:
            self.selected_cards = []
            self.update_interface()
            
            # 如果游戏没有结束，检查下一个玩家是否是AI
            if not self.game.finished and self.game.current_player in self.game.ai_players:
                self.root.after(1000, self.ai_play)  # 延迟1秒让AI思考
        else:
            messagebox.showerror("错误", f"出牌失败: {message}")
    
    def pass_turn(self):
        """过牌操作"""
        success, message = self.game.play_turn(None)
        if success:
            self.selected_cards = []
            self.update_interface()
            
            # 如果游戏没有结束，检查下一个玩家是否是AI
            if not self.game.finished and self.game.current_player in self.game.ai_players:
                self.root.after(1000, self.ai_play)  # 延迟1秒让AI思考
        else:
            messagebox.showerror("错误", f"过牌失败: {message}")
    
    def ai_play(self):
        """AI玩家回合"""
        if self.game.finished:
            return
        
        # 标记AI正在思考
        self.ai_thinking = True
        self.status_label.config(text=f"AI玩家 {self.game.current_player} 正在思考...")
        self.root.update()
        
        # 延迟一下，让玩家看到AI在思考
        self.root.after(1500, self.execute_ai_move)
    
    def execute_ai_move(self):
        """执行AI移动"""
        if self.game.finished:
            return
        
        # AI进行回合
        success, message = self.game.ai_play_turn()
        
        # 更新界面
        self.update_interface()
        
        # 添加AI操作到历史
        self.history_text.config(state=tk.NORMAL)
        if success:
            if self.game.last_played:
                cards = ", ".join(self.game.last_played[1])
                self.history_text.insert(tk.END, f"AI {self.game.current_player} 出牌: {cards}\n")
            else:
                self.history_text.insert(tk.END, f"AI {self.game.current_player} 选择过牌\n")
        else:
            self.history_text.insert(tk.END, f"AI {self.game.current_player} 操作失败: {message}\n")
        self.history_text.config(state=tk.DISABLED)
        
        # 滚动到历史底部
        self.history_text.see(tk.END)
        
        # 如果游戏没有结束，检查下一个玩家是否是AI
        if not self.game.finished and self.game.current_player in self.game.ai_players:
            self.root.after(1000, self.ai_play)  # 延迟1秒让下一个AI思考
        else:
            self.ai_thinking = False

# 启动游戏
if __name__ == "__main__":
    app = BigTwoGUI()