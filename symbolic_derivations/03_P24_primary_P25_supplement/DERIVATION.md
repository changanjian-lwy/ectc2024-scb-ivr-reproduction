# P24主＋P25辅：四相轮转符号模型草案

## 详细推导入口

1. `01_FULL_MODULE_EQUATIONS.md`：单模块四相接线、七节点KCL、电容矩阵、六阶段DAE与边界。
2. `02_LOCAL_REDUCTIONS.md`：从整体模块降阶的M2/M5公式，以及另行隔离单元的近似。两种局部模型分开。
3. `03_CONDUCTION_BALANCE_AND_LIMITS.md`：有限飞跨电容导通解、电荷平衡、条件变比与时序预算。
4. `verify_matrix_structure.py`：无量纲占位测试，检查矩阵接线和降阶回代，不作器件仿真。
5. `04_A43_H2_ANALYTICAL_AUDIT.md`：用完整模块降阶解释A43的1.418 V残余电压，附旧数据提取与计算脚本。

当前只分析nM_instance=1，没有模块间耦合。下文是概要，详细文件的边界与限定优先。

P24提供四相功率级；P25补充全非工作相低侧导通及下一相事件顺序。低侧Source接公共地是当前明确采用的补充解释。四相旋转是外延，不是P24已完整报道的门极向量。

## 开关顺序

工作相k高侧ON、低侧OFF，其他高侧OFF、低侧ON；工作高侧OFF后进行本相低侧换流；低侧准入后全部低侧ON；监测下一相r=k mod nP+1过零并建立负电流；达到αIpk后关闭低侧r；下一高侧r满足Vds=0才准入并锁存。

该顺序不能标为P24原生。α需保持P24与P25来源标签；时序与电流规则的组合也必须标为交叉论文假设。

## 导通阶段节点与搬运电荷

定义边界vC0=Vin、vC,nP=0；它们是符号端点，不是新增电容。nP=4时：

    u1=Vin-vC1
    u2=vC1-vC2
    u3=vC2-vC3
    u4=vC3
    Lk dik/dt=uk-Vo
    Σ uk=Vin

不预设各uk相等。理想高侧导通期间，对实际存在的相邻飞跨电容：

    Ck dvCk/dt=ik
    Ck-1 dvCk-1/dt=-ik
    duk/dt=-ik(1/Ck-1+1/Ck)

端点Vin和0刚性，端点倒数电容项按0处理。定义1/Ctr,k=1/Ck-1+1/Ck，则：

    d²ik/dt²=-ik/(Lk Ctr,k)

短时冻结电容电压且ik,start=0时：

    ik≈(uk-Vo)τ/Lk
    Qk≈(uk-Vo)Ton,k²/(2Lk)

初始电流不为零时需加ik,start Ton,k。每个飞跨电容的导通贡献：ΔvCj=(Qj-Qj+1)/Cj；完整周期还需计入换流电荷。

## 有条件的均衡规律

正工作电流使uk下降；相邻搬运电荷差使vCj调整。若所有相的L、Ton、初始电流和换流贡献具有相应对称性，周期电荷平衡可支持相等uk的候选状态。不能仅由Σuk=Vin就推出uk=Vin/nP，也不能据此证明渐近稳定或零启动。

忽略换流、低侧节点为0且高侧uk近似恒定时，伏秒平衡为Dk uk=Vo。仅在额外得到uk=Vin/nP后才有D=nP Vo/Vin。这是条件推导，不是预先定义有效电压来强迫变比。

## 换流与后续审计

已完成的详细推导与审计：

- `01_FULL_MODULE_EQUATIONS.md`：完整节点KCL及电容矩阵。
- `02_LOCAL_REDUCTIONS.md`：受门极约束的局部消元及ZVS条件。
- `03_CONDUCTION_BALANCE_AND_LIMITS.md`：导通搬运、电荷平衡与适用限制。
- `04_A43_H2_ANALYTICAL_AUDIT.md`：已有7.77%案例的H2审计。
- `05_FOUR_POSITIONS_AND_9PCT_CROSSCHECK.md`：四个位置的电容差异，以及已有9%案例的能量/时序失败分类。
- `06_H3_ZVS_WINDOW_AND_RECHARGE.md`：首次上侧钳位、退出与电压回升。
- `07_H3_FIXED_SLOT_FEASIBILITY.md`：释放时刻与负电流绑定的100 ns窗口解析求解，未新跑SPICE。
- `08_TIMING_GUARD_SOURCE_AUDIT.md`：固定时隙守卫的文献依据及实现选择区分。
- `09_PREDECESSOR_STATE_AND_PERIOD_CONSTRAINTS.md`：H2/H3前序初值必要条件与旧RAW伏秒积分核对。
- `10_JOINT_RESIDUAL_CONTRACT_AND_OLD_CASE_AUDIT.md`：复用旧联合求解经验，补充全节点/控制状态闭合和最早失效分类。
- `11_REDUCED_CYCLE_CONSTRAINT_CONFLICT.md`：分段局部周期计算，固定Ton无200 ns根及可变Ton的峰值/均流代价。
- `12_FINITE_FLYING_CAP_FULL_MATRIX_INTERVAL.md`：完整节点矩阵固定模式推进、有限飞跨动态及实际节点电压积分对照。
- `13_RON_REVERSE_BRANCH_VOLTAGE_BUDGET.md`：原库Ron/反向I-V全节点推进、相间电压预算及旧波形核对。
- `14_CONTINUOUS_H2_H3_REPLAY_AND_EARLIER_ORDER_FAILURE.md`：无阶段重置连续复现H3失败，标出更早的下一相过零顺序入口违例。
- `15_H3_CANDIDATE_FEASIBILITY_AND_H4_FAILURE.md`：独立L3前序状态候选，H3局部通过、H4及整环仍未通过。
- `16_ONE_RING_ADMISSION_BUT_NOT_PERIODIC.md`：三批独立候选计算、一轮全准入、状态/功率未闭合及第二轮最早失败。
- `17_FEASIBLE_FIXED_POINT_NEWTON_SEARCH.md`：全11状态固定点局部搜索、可行边界阻碍及容差核对，未收敛。
- `18_CONSTRAINED_DESCENT_AND_NUMERICAL_EDGE.md`：显式约束找到可行下降方向，残差降低但准入贴边/功率未达标。
- `19_MARGIN_RETAINING_DESCENT.md`：保留相对准入余量仍可降低残差，但H2仅飞秒级余量，周期仍未闭合。
- `20_COMPLETE_ZVS_WINDOWS.md`：完整保持关断窗口审计；H2窗口约170 ps，飞秒级数字仅是固定时隙相对左端的余量。
- `21_CONTINUATION_AND_SECOND_RING_FAILURE.md`：延续8步残差降低20.4%，窗口位置代价及第二轮H3在300 ns最早准入失败。
- `22_MATHEMATICAL_BASIS_AND_FIXED_MARGIN.md`：数学依据等级、结构/故意错误核验及固定参考余量搜索，残差继续降低但仍未闭合。
- `23_MINIMUM_LEAD_SEARCH_AND_TRADEOFF.md`：五组辅助优化约束对照；H2左余量提高、残差降低，但节点回归/功率有代价，第二轮仍失败。
- `24_NODE_RETURN_CONSTRAINTS_AND_LOCAL_CONDITIONING.md`：加入节点回归上限后23步候选改善、局部数值条件与原准入诊断；第二轮仍失败，未闭合。
- `25_EVENT_CONTROL_SOURCE_L_AND_PERIODICITY_AUDIT.md`：文献衍生L选择、独立事件控制/联合控制搜索与长运行核验；19整轮后提前过零失败，未复现。
- `26_FIXED_SPACING_L_CONTINUATION_AND_POWER_CONFLICT.md`：恢复50 ns均匀交错后逐步降低L、严格检查5–10%范围；延续至98.5%但长运行及250 W联合目标仍失败。
- `27_IDEAL_TABLE_REFERENCE_AND_PEAK_DEFICIT.md`：P24理想三角波基准严格恢复250 W，并用KVL把详细夹具的峰值缺口拆为负初始电流和有效相节点电压不足。
- `28_CHARGE_BALANCE_RESISTANCE_AND_SEQUENCE_BRANCH.md`：把长期失效定位为飞跨电荷不平衡，拒绝不闭合的Ron延续点，并建立P24相邻低侧/P25全非活动低侧两个明确分支。
- `29_LOCAL_PHASE_VS_GLOBAL_HANDOFF_MAPPING.md`：区分P24同一相的200 ns三阶段与P25相邻相的50 ns全局交接，固定物理事件映射并禁止按`t`标签硬对齐。

多相M2/M5采用完整节点KCL，保留所有相电流与开关Coss；共同局部LC模板只用于隔离诊断。当前已推进至完整连续事件环及周期回归搜索，下一步审计周期闭合与最小ZVS准入余量的取舍，不把局部Ceq直接推广到四相。
