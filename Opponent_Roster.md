# 精灵图鉴：对手 + 我方（`bots/teams/*.txt` + `players/wche652.py` 解析）

> 5 档对手队伍（uber/ou/uu/ru/nu，共 30 只，`Zapdos-Galar` 在 ru/nu 重复）+ 我方现在这套 6 人队伍，
> 逐招式解析实际效果。属性(type)、特性、招式效果是按 Gen9 官方数据补充的，队伍文本本身只写了名字。
> 这份是给 `_choose_move` 规则设计用的素材——知道每个招式具体干什么，才能写"遇到瘫痪怎么办""对面撒钉子要不要理"这类判断。

---

# 第一部分：对手（`bots/teams/*.txt`）

## Uber 档

### Deoxys-Speed（超能力）
特性 Pressure（消耗对方 PP 更快） / 道具 Focus Sash（濒死一击会保留 1 HP，仅限满血时触发一次） / 太晶：幽灵
- **Thunder Wave 电磁波**：变化招式，使目标陷入瘫痪（速度减半、25% 概率无法行动）。对电系/地面系无效（免疫）。
- **Spikes 撒菱**：在对方场地铺钉子，最多叠 3 层，对方每次换人上场（非飞行/非悬浮）都会扣血。
- **Taunt 挑衅**：几回合内封锁目标使用变化招式的能力。
- **Psycho Boost 精神先制**：超能力特殊招式，威力 140（很高），命中后**自己特攻 -2**（跟绝地大反攻/过热是同一类"一次性爆发"招式，不是先制招）。

### Kingambit（恶/钢）
特性 Supreme Overlord（每有一只队友倒下，攻击力提升） / 道具 Dread Plate（提升恶系招式威力） / 太晶：恶
- **Swords Dance 剑舞**：自己攻击 +2。
- **Kowtow Cleave 拜首劈落**：恶系物理，威力 85，**必定命中**（不判定命中率）。
- **Iron Head 铁头**：钢系物理，威力 80，有几率使目标畏缩。
- **Sucker Punch 突袭**：恶系物理，**先制 +1**，但只有当目标这回合准备使用攻击招式时才会命中，否则直接失败。

### Zacian-Crowned（妖精/钢）
特性 Intrepid Sword（首次上场自己攻击 +1） / 道具 Rusted Sword（专属，不可被拍落/交换剥夺） / 太晶：飞行
- **Swords Dance 剑舞**：自己攻击 +2。
- **Behemoth Blade 圣剑**：钢系物理，威力 100，签名招式，纯粹高威力输出。
- **Close Combat 近身战**：格斗系物理，威力 120，命中后**自己防御/特防各 -1**。
- **Wild Charge 野性电流**：电系物理，威力 90，造成伤害后**自己受到 1/4 反作用力伤害**。

### Arceus-Fairy（妖精）
特性 Multitype（属性随所持神石变化） / 道具 Pixie Plate（决定其为妖精属性，同时提升妖精系招式威力） / 太晶：火
- **Calm Mind 冥想**：自己特攻/特防各 +1。
- **Judgment 制裁之光**：属性随神石变化（这里是妖精系）特殊招式，威力 100，签名招式。
- **Taunt 挑衅**：封锁对方变化招式。
- **Recover 生命种子（自我再生）**：回复 50% 最大 HP。

### Eternatus（毒/龙）
特性 Pressure（消耗对方 PP 更快） / 道具 Power Herb（跳过蓄力招式的蓄力回合，效果发动后消耗掉） / 太晶：火
- **Agility 电光一闪（应为"高速移动"）**：自己**速度 +2**，纯变速招式，**没有先制效果**。
- **Meteor Beam 陨石光束**：岩石系特殊，正常需要"第一回合蓄力（同时自己特攻 +1）、第二回合才攻击"，但配合 Power Herb 可以**当回合直接打出，且仍然获得特攻 +1**。
- **Dynamax Cannon 龙星群**：龙系特殊，签名招式，威力 100，游戏内设定是对极巨化目标双倍伤害——**但 Gen9 没有极巨化机制，所以实战就是一个正常的 100 威力招式**。
- **Fire Blast 十万马力（应为"大字爆炎"）**：火系特殊，威力 110，命中率 85%，有几率烧伤。

### Koraidon（格斗/龙）
特性 Orichalcum Pulse（顺光下自己攻击提升，同时开局自动唤起晴天） / 道具 Life Orb（招式威力 +30%，但每次攻击后自己损失 1/10 最大 HP） / 太晶：火
- **Swords Dance 剑舞**：自己攻击 +2。
- **Scale Shot 鳞片射击**：龙系物理，连续攻击 2~5 次，**打完之后自己速度 +1、防御 -1**。
- **Flame Charge 火花冲锋（应为"蓄能爆炎"）**：火系物理，威力 50，命中后**自己速度 +1**。
- **Close Combat 近身战**：格斗系物理，威力 120，命中后自己防御/特防各 -1。

**这一档要点**：`Zacian-Crowned`/`Koraidon` 剑舞一次起飞就很难拦；`Deoxys-Speed` 开局先手电磁波+钉子最烦人，能先手秒掉或者免疫瘫痪最好；`Arceus-Fairy` 冥想+回血组合理论上拖久了会滚雪球，**但这条只适用于真人/会做判断的对手**——`bots/max_damage.py` 的源码是纯粹"选当前威力最高的招式"（`max(available_moves, key=lambda m: m.base_power)`），冥想/回血威力都是 0，只要 Judgment（100 威力）还有 PP，`max_damage-uber` 这个具体 bot 永远不会用冥想或回血，叠盾/回血这套威胁对它不成立。`max_damage-uber` 打得久单纯是双方磨伤害磨得慢，不是叠盾——这个区分 2026-07-23 验证过（Taunt 反叠盾修复对这个对手完全没有效果，才回头查的 bot 源码），`simple`/`random` 两种风格没有查过，不确定是否也是这个结论。

---

## OU 档

### Ogerpon-Wellspring（草/水，戴面具后天赋属性）
特性 Water Absorb（受到水系攻击时回血而非受伤） / 道具 Wellspring Mask（决定属性为水，专属不可拍落） / 太晶：水
- **Ivy Cudgel 常春藤攻击**：物理招式，属性随所戴面具变化（这里是水系），威力 100，**高暴击率**。
- **Knock Off 拍落**：恶系物理，若目标持有道具则威力提升，命中后**永久移除目标的持有物**（专属变身道具除外）。
- **U-turn U 型回转**：虫系物理，命中后**立刻换人**。
- **Spikes 撒菱**：铺钉子，最多 3 层。

### Garganacl（岩石）
特性 Purifying Salt（免疫异常状态，受幽灵系攻击伤害减半） / 道具 Leftovers（每回合回复 1/16 最大 HP） / 太晶：妖精
- **Salt Cure 盐渍**：岩石系物理，命中后额外附加"腌渍"效果，之后每回合目标额外掉血（对钢/水系伤害更高）。
- **Stealth Rock 隐形岩**：铺设岩钉，对方每次换人上场按岩石系克制关系扣血（不需要脚落地，飞行系也会中招）。
- **Protect 守住**：本回合免疫一切攻击和大部分效果，连续使用成功率会下降。
- **Recover 生命种子**：回复 50% 最大 HP。

### Great Tusk（地面/格斗）
特性 Protosynthesis（晴天或持有增强镜时最高能力值提升） / 道具 Heavy-Duty Boots（免疫场地钉子类效果） / 太晶：冰
- **Headlong Rush 逆头猛撞**：地面系物理，威力 120（很高），命中后**自己防御/特防各 -1**。
- **Ice Spinner 冰锥旋转**：冰系物理，威力 80，命中后**清除自己这边场地的钉子**。
- **Knock Off 拍落**：见上，移除目标持有物。
- **Rapid Spin 高速旋转**：一般系物理，命中后清除自己这边的钉子/绑定效果，并**自己速度 +1**。

### Dragonite（龙/飞行）
特性 Multiscale（满血时受到的伤害减半） / 道具 Heavy-Duty Boots（免疫钉子） / 太晶：一般
- **Extreme Speed 二连极速（应为"神速"）**：一般系物理，**先制 +2**，威力 80，是最优先动作的招式之一。
- **Earthquake 地震**：地面系物理，威力 100，对飞行系/悬浮特性无效。
- **Ice Spinner 冰锥旋转**：见上。
- **Dragon Dance 龙之舞**：自己攻击/速度各 +1。

### Moltres（火/飞行）
特性 Flame Body（被物理接触攻击时有几率反烧对方） / 道具 Heavy-Duty Boots（免疫钉子） / 太晶：妖精
- **Flamethrower 喷射火焰**：火系特殊，威力 90，有几率烧伤。
- **Brave Bird 勇鸟猛攻**：飞行系物理，威力 120，**自己承受 1/3 反作用力伤害**。
- **Roost 燕返**：回复 50% 最大 HP，**使用当回合自己暂时失去飞行属性**（防御端影响：不再免疫地面系攻击）。
- **Will-O-Wisp 玩火**：使目标陷入烧伤（物理攻击力减半 + 每回合掉血），对火系无效。

### Darkrai（恶）
特性 Bad Dreams（对方陷入睡眠时每回合额外掉血） / 道具 **Choice Scarf**（速度 ×1.5，但**只能使用选中的第一个招式**，直到换人才能改） / 太晶：毒
- **Dark Pulse 恶之波动**：恶系特殊，威力 80，有几率畏缩。
- **Ice Beam 冰冻光束**：冰系特殊，威力 90，有几率冻伤。
- **Sludge Bomb 污泥炸弹**：毒系特殊，威力 90，有几率中毒。
- **Trick 戏法**：与目标**互换持有物**（可以把 Choice Scarf 甩给对方，让对方也被锁招式）。

**这一档要点**：`Dragonite` 满血时防御力翻倍（Multiscale），先手削一口血再打性价比更高；`Darkrai` 是 Scarf 提速爆发，出场先当心它抢先手；出招后 Darkrai 这回合的招式就固定了，摸清楚第一次用的什么招后面几回合可以放心针对。

---

## UU 档

### Tornadus-Therian（飞行）
特性 Regenerator（换下场时回复 1/3 最大 HP） / 道具 Heavy-Duty Boots（免疫钉子） / 太晶：钢
- **Nasty Plot 邪恶之心**：自己特攻 +2。
- **Hurricane 暴风**：飞行系特殊，威力 110，命中率 70%（雨天必中、晴天命中率再降），有几率混乱。
- **U-turn U 型回转**：命中后换人。
- **Focus Blast 冥想拳（应为"真气拳"）**：格斗系特殊，威力 120，命中率仅 70%，有几率降低目标特防。

### Clodsire（毒/地面）
特性 Water Absorb（受水系攻击回血） / 道具 Heavy-Duty Boots（免疫钉子） / 太晶：妖精
- **Earthquake 地震**：见上，威力 100。
- **Poison Jab 毒电击拳（应为"毒击拳"）**：毒系物理，威力 80，有几率中毒。
- **Spikes 撒菱**：铺钉子。
- **Recover 生命种子**：回复 50% 最大 HP。

### Metagross（钢/超能力）
特性 Clear Body（能力等级不会被对方招式/特性降低） / 道具 **Choice Band**（攻击 ×1.5，锁定第一个使用的招式） / 太晶：钢
- **Bullet Punch 子弹拳**：钢系物理，**先制 +1**，威力 40。
- **Heavy Slam 重金属爆炸（应为"重压"）**：钢系物理，威力随"自己体重/目标体重"比值变化，体重差越大威力越高（Metagross 很重，通常能打出高威力）。
- **Knock Off 拍落**：见上。
- **Psychic Fangs 精神利牙**：超能力系物理，威力 85，命中后**顺带破坏目标场上的反射壁/光墙**。

### Rotom-Wash（电/水）
特性 Levitate（免疫地面系招式） / 道具 Leftovers（每回合回血 1/16） / 太晶：钢
- **Hydro Pump 水炮**：水系特殊，威力 110，命中率仅 80%。
- **Volt Switch 伏特替换**：电系特殊，命中后换人。
- **Thunder Wave 电磁波**：使目标瘫痪，对电系/地面系无效。
- **Pain Split 分身撞击（应为"分摊痛楚"）**：非伤害招式，把自己和目标的当前 HP 数值拉平（各变成两者平均值），HP 差距越大对使用者越有利。

### Cobalion（钢/格斗）
特性 Justified（受到恶系攻击时自己攻击 +1） / 道具 Rocky Helmet（被物理接触攻击时反弹 1/6 最大 HP 伤害给对方） / 太晶：水
- **Stealth Rock 隐形岩**：见上。
- **Body Press 恶意波动（应为"扑击"）**：格斗系物理，**伤害计算用自己的防御数值而非攻击数值**，防御堆得越高伤害越高。
- **Volt Switch 伏特替换**：见上，命中后换人。
- **Thunder Wave 电磁波**：见上，使目标瘫痪。

### Zarude-Dada（恶/草）
特性 Leaf Guard（晴天下免疫异常状态） / 道具 Heavy-Duty Boots（免疫钉子） / 太晶：妖精
- **Swords Dance 剑舞**：自己攻击 +2。
- **Knock Off 拍落**：见上。
- **Power Whip 强力鞭打**：草系物理，威力 120，命中率 85%。
- **Jungle Healing 丛林治疗**：回复自己（及友方，单打里只对自己生效）50% HP，**并治愈异常状态**。

**这一档要点**：钉子/瘫痪密度全场最高（`Clodsire`/`Cobalion` 都撒钉子，`Rotom-Wash`/`Cobalion` 都会电磁波），带清钉/免疫瘫痪的手段能省很多事；`Cobalion` 的 Body Press 用防御打伤害，物理防御堆得高的话打我们高防御精灵反而更疼，别用"防御高就不怕物理"的思路轻视它。

---

## RU 档

### Rotom-Heat（电/火）
特性 Levitate（免疫地面系） / 道具 Heavy-Duty Boots（免疫钉子） / 太晶：钢
- **Volt Switch 伏特替换**：命中后换人。
- **Overheat 过热**：火系特殊，威力 130（很高），命中后**自己特攻 -2**。
- **Will-O-Wisp 玩火**：使目标烧伤。
- **Pain Split 分摊痛楚**：见上，拉平双方 HP。

### Krookodile（地面/恶）
特性 **Intimidate（上场时使对方攻击 -1）** / 道具 Leftovers（每回合回血） / 太晶：幽灵
- **Stealth Rock 隐形岩**：见上。
- **Earthquake 地震**：威力 100。
- **Knock Off 拍落**：见上。
- **Taunt 挑衅**：封锁对方变化招式。

### Slowbro（水/超能力）
特性 Regenerator（换下场回血 1/3） / 道具 Rocky Helmet（反弹接触伤害） / 太晶：妖精
- **Scald 万里波涛（应为"沸水"）**：水系特殊，威力 80，有几率烧伤对方（**物理输出手被烧伤=攻击腰斩，很致命**）。
- **Future Sight 预知未来**：设下延迟攻击，**两回合后**对当时场上的目标（不管中途是否换人）造成一次超能力特殊伤害，不受当下场面状态影响。
- **Thunder Wave 电磁波**：使目标瘫痪。
- **Slack Off 睡觉回血（应为"偷懒"）**：回复 50% 最大 HP。

### Cyclizar（龙/一般）
特性 Regenerator（换下场回血 1/3） / 道具 Assault Vest（特防 ×1.5，但**无法使用任何变化招式**） / 太晶：毒
- **Double-Edge 舍身冲撞（应为"舍身撞击"）**：一般系物理，威力 120，**自己承受 1/3 反作用力伤害**。
- **Rapid Spin 高速旋转**：清钉子，自己速度 +1。
- **Knock Off 拍落**：见上。
- **U-turn U 型回转**：命中后换人。

### Jirachi（钢/超能力）
特性 Serene Grace（招式的附加效果发生几率翻倍） / 道具 Leftovers（每回合回血） / 太晶：格斗
- **Psychic Noise 精神噪音**：超能力系特殊，命中后使目标**接下来几回合无法通过回血招式/特性/道具回复 HP**。
- **Aura Sphere 冥想拳（应为"波导弹"）**：格斗系特殊，威力 80，**不判定命中率，必定命中**。
- **Thunderbolt 十万伏特**：电系特殊，威力 90，有几率瘫痪（配合 Serene Grace，几率翻倍到 20% 左右）。
- **Calm Mind 冥想**：自己特攻/特防各 +1。

### Zapdos-Galar（格斗/飞行）
特性 **Defiant（能力等级被对方招式/特性降低时，自己攻击 +2 作为反弹）** / 道具 **Choice Scarf**（速度 ×1.5，锁招） / 太晶：飞行
- **Close Combat 近身战**：格斗系物理，威力 120，命中后自己防御/特防各 -1。
- **Brave Bird 勇鸟猛攻**：飞行系物理，威力 120，自己承受 1/3 反作用力伤害。
- **Knock Off 拍落**：见上。
- **U-turn U 型回转**：命中后换人。

**这一档要点**：`Krookodile` 一上场就用 Intimidate 砍我方物理输出手一级攻击；`Slowbro` 的 Scald 烧伤对物理手杀伤力很大；`Zapdos-Galar` 带 Defiant，**打它时避免使用降低其能力等级的招式**（比如吼叫式的降属性招式、Intimidate 类特性触发都会让它反而攻击暴涨），拍落/直接输出没问题。

---

## NU 档

### Entei（火）
特性 Inner Focus（免疫畏缩效果） / 道具 Heavy-Duty Boots（免疫钉子） / 太晶：一般
- **Extreme Speed 神速**：先制 +2，威力 80。
- **Sacred Fire 圣火**：火系物理，威力 100，命中率 95%，小几率烧伤。
- **Stone Edge 尖石攻击**：岩石系物理，威力 100，命中率 80%，高暴击率。
- **Double-Edge 舍身撞击**：威力 120，自己承受 1/3 反作用力。

### Chesnaught（草/格斗）
特性 Bulletproof（免疫弹丸/炸弹类招式，如污泥炸弹、极巨火花等） / 道具 Rocky Helmet（反弹接触伤害） / 太晶：幽灵
- **Body Press 扑击**：格斗系物理，用自己防御数值算伤害。
- **Knock Off 拍落**：见上。
- **Spikes 撒菱**：铺钉子。
- **Synthesis 光合作用**：回血，回复量受天气影响（晴天回更多，雨/沙/雪回更少）。

### Volcanion（火/水）
特性 Water Absorb（受水系攻击回血） / 道具 Heavy-Duty Boots（免疫钉子） / 太晶：恶
- **Flamethrower 喷射火焰**：威力 90，几率烧伤。
- **Steam Eruption 蒸气爆炸**：水系特殊，威力 110，几率烧伤，**若自己处于冰冻状态会解冻**。
- **Roar 咆哮**：**强制目标换成随机一只其他精灵**（无视场地/替身等大部分保护效果），**先制 -6**，全场最后行动。
- **Earth Power 大地之力**：地面系特殊，威力 90，几率降低目标特防。

### Muk-Alola（毒/恶）
特性 Poison Touch（物理接触攻击有几率使目标中毒） / 道具 Leftovers（每回合回血） / 太晶：钢
- **Poison Jab 毒击拳**：威力 80，几率中毒。
- **Knock Off 拍落**：见上。
- **Rest 睡觉**：**完全回满 HP + 清除异常状态**，但自己进入 2 回合睡眠。
- **Sleep Talk 睡梦呓语**：**只能在自己睡眠状态下使用**，随机打出自己其他三个招式中的一个（等于带睡眠状态硬出招）。

### Bronzong（钢/超能力）
特性 Levitate（免疫地面系） / 道具 Leftovers（每回合回血） / 太晶：妖精
- **Body Press 扑击**：用防御数值算物理伤害。
- **Psychic Noise 精神噪音**：命中后封锁目标回血手段。
- **Iron Defense 铁壁**：自己防御 +2。
- **Stealth Rock 隐形岩**：铺岩钉。

### Zapdos-Galar（同 ru 档，见上）

**这一档要点**：`Muk-Alola` 的 Rest + Sleep Talk 组合能一边回满血一边继续输出，硬吃很麻烦，最好一次性能打掉大半血或者绕开；`Volcanion` 的 Roar 会打乱我方场面节奏（强制换人），要提防它在关键时刻把我方后手精灵逼出来。

---

# 第二部分：我方队伍（`showdown_agent/scripts/players/wche652.py`）

### Ribombee（虫/妖精）
特性 Shield Dust（免疫招式的附加效果，比如冰冻光束不再有几率冻伤自己） / 道具 Focus Sash（满血时被一击击破会保留 1 HP） / 太晶：钢
- **Stun Spore 麻痹粉**：草系变化招式，使目标瘫痪；**对草系无效**（Ribombee 自己不受影响，但对面若是草系精灵这招会打空）。
- **U-turn U 型回转**：命中后换人，可以在侦查完对手阵容后安全撤退。
- **Moonblast 月亮之力**：妖精系特殊，威力 95，几率降低目标特攻。
- **Sticky Web 黏黏网**：**在对方场地铺设**，之后对方每次换人上场速度 -1（不掉血，纯削速度，对飞行系依然生效除非有大地之杖之类的免疫）。

### Koraidon（格斗/龙）
（与 uber 档对手队伍里那只属性/特性/签名机制相同，只是道具不同）道具 Loaded Dice（多段攻击招式必定命中较多次数，且不再需要担心低命中的多段招式漏打） / 太晶：火
- **Swords Dance 剑舞**：自己攻击 +2。
- **Scale Shot 鳞片射击**：连续攻击 2~5 次（配合 Loaded Dice 基本稳定命中 4~5 次），打完自己速度 +1、防御 -1。
- **Flare Blitz 闪焰冲锋**：火系物理，威力 120，自己承受 1/3 反作用力，几率烧伤对方。
- **Taunt 挑衅**：封锁对方变化招式，能防止对面开钉子/回血苟活。

### Arceus-Ghost（幽灵）
特性 Multitype（属性随神石变化，这里是幽灵） / 道具 Spooky Plate（决定幽灵属性，提升幽灵系招式威力） / 太晶：星晶（Stellar，太晶后对任意属性都有一次超效果加成）
- **Judgment 制裁之光**：幽灵系特殊，签名招式，威力 100。
- **Aura Sphere 波导弹**：格斗系特殊，威力 80，必定命中。
- **Power Gem 宝石光**：岩石系特殊，威力 80，无附加效果，纯输出覆盖面。
- **Calm Mind 冥想**：自己特攻/特防各 +1，适合当收尾核心。

### Zacian-Crowned（妖精/钢）
（与 uber 档对手队伍那只完全同款配置）道具 Rusted Sword（专属，不可被拍落） / 太晶：飞行
- **Swords Dance 剑舞**：自己攻击 +2。
- **Close Combat 近身战**：格斗系物理，威力 120，命中后自己防御/特防各 -1。
- **Behemoth Blade 圣剑**：钢系物理，威力 100，签名招式。
- **Wild Charge 野性电流**：电系物理，威力 90，自己受到 1/4 反作用力。

### Eternatus（毒/龙）
（与 uber 档对手队伍同款）道具 Power Herb（跳过蓄力招式的蓄力回合，用一次少一次） / 太晶：火
- **Sludge Bomb 污泥炸弹**：毒系特殊，威力 90，几率中毒。
- **Meteor Beam 陨石光束**：配合 Power Herb 当回合直接打出，且自己特攻 +1。
- **Dynamax Cannon 龙星群**：龙系特殊，威力 100，Gen9 里就是纯 100 威力招式。
- **Fire Blast 大字爆炎**：火系特殊，威力 110，命中率 85%，几率烧伤。

### Kyogre（水）
特性 Drizzle（**上场时自动唤起雨天**，持续 5 回合；本队水系招式在雨天下威力 ×1.5，火系招式威力减半） / 道具 **Choice Band**（攻击 ×1.5，锁定第一个使用的招式） / 太晶：妖精
- **Waterfall 瀑布攀登**：水系物理，威力 80（雨天下等效威力约 120），小几率畏缩。
- **Body Slam 泰山压顶**：一般系物理，威力 85，几率瘫痪，对处于"缩小"状态的目标双倍伤害。
- **Earthquake 地震**：地面系物理，威力 100，对飞行系/悬浮特性无效。
- **Tera Blast 太晶爆发**：一般系特殊招式，**太晶化后属性变为自己的太晶属性（这里是妖精），且攻击/特攻取较高者作为伤害计算的能力值类别**，威力 80。

**我方队伍要点**：
- **两个 Choice 系锁招（Kyogre 的 Choice Band）+ 两个剑舞速攻手（Koraidon/Zacian-Crowned）+ 一个奶盾（Arceus-Ghost）+ 一个开场支援（Ribombee 撒钉+瘫痪）**，整体是"支援铺垫 + 双爆发核心 + 特殊输出补漏 + 盾"的结构。
- `Kyogre` 上场自动下雨，会同时削弱队伍里 `Koraidon`/`Zacian-Crowned` 的火系招式（Flare Blitz 威力打折），排出场顺序或者太晶时机时要考虑这个天气联动。
- `Zacian-Crowned` 的 Rusted Sword、`Arceus-Ghost`/`Eternatus` 用的神石/魂香类道具，都是"专属不可拍落"道具，面对对手一堆 Knock Off 时这几只不用担心掉装备，`Kyogre` 的 Choice Band 和 `Koraidon` 的 Loaded Dice 会怕拍落，规则里可以考虑"道具被拍掉之后行为要不要调整"。

---

# 跨档通用观察（对写规则最有用的几条）

- **拍落（Knock Off）出现频率极高**（uber 档之外几乎每档都有 1~2 只）：会打掉持有物且不可恢复（专属变身道具除外）。我方 `Kyogre`（Choice Band）、`Koraidon`（Loaded Dice）怕这个，`Zacian-Crowned`/`Arceus-Ghost`/`Eternatus` 的道具是专属道具，不怕。
- **撒钉子的对手非常多**（几乎每档都有 1~2 个）：我方队伍目前**没有任何清钉/免疫钉子的手段**（没人带 Heavy-Duty Boots，也没有 Rapid Spin/Defog），频繁换人会一直掉血，这是个明显的队伍短板，值得回头考虑。
- **电磁波瘫痪出现在 3 个不同档位**（`Cobalion`/`Rotom-Wash`/`Slowbro`）：瘫痪对速度依赖大的 `Koraidon`/`Zacian-Crowned` 杀伤力很大，规则里可以加一条"被瘫痪时有 25% 概率被跳过，优先选保险的招式"。
- **`Zapdos-Galar` 带 Defiant，出现在 ru 和 nu 两档**：打它时不要用降低其能力等级的招式（我方 `Ribombee` 的 `Moonblast` 会降对方特攻，`Koraidon`/`Arceus-Ghost` 没有降能力招式，这条主要是提醒别用 Moonblast 打它）。
- **不少对手是 Choice 系列锁招**（`Darkrai`/`Metagross`/`Zapdos-Galar` 都是 Scarf/Band）：摸清楚它第一次出招类型后，后面几回合可以放心针对性接招——这跟我方 `Kyogre` 自己也是 Choice Band 是同一个道理，双方都要面对"锁招"的博弈。
- **我方 `Kyogre` 的 Drizzle 天气会跟自己队伍里的火系招式打架**（`Koraidon` 的 `Flare Blitz`、`Eternatus`/`Zacian-Crowned` 都可能受影响），出场顺序和太晶时机的规则要把这个天气联动考虑进去。
