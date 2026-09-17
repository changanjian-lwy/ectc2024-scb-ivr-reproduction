# P25原生：三相六模态方程草案

依据：P25 Fig.2/3与六模态文字；项目转录见p25_operating_supplement.py。nP=3，nM保留；不是四相外延。

## 开关与事件

| 模态 | 导通命令 | 终止事件 |
|---|---|---|
| M1 | SH1、SL2、SL3 | SH1导通时间结束 |
| M2/2′ | SL2、SL3；第一相换流 | SL1达到零电压并准入 |
| M3 | SL1、SL2、SL3 | 下一相i2过零 |
| M4 | SL1、SL2、SL3 | i2达到目标负值 |
| M5/5′ | SL1、SL3；第二相换流 | SH2达到零电压并准入 |
| M6 | SL1、SH2、SL3 | SH2导通时间结束 |

α保留符号；模态文字5%-10%与设计段其他表述需分别引用，不能以某个扫描值取代论文规则。时间标签以物理事件映射，不能因原文标号不一致改动事件。

## 理想高侧导通子区间

按原生三相系列电容结构、非工作相低侧接地：

    u1=Vin-vC1, u2=vC1-vC2, u3=vC2
    Lk dik/dt=uk-Vo

M1内：C1 dvC1/dt=i1。M6内：C1 dvC1/dt=-i2，C2 dvC2/dt=i2。第三相导通时C2 dvC2/dt=-i3。这些式子忽略关断器件Coss电流，不能用于换流区间。

低侧导通的各相满足Lk dik/dt=-Vo；下一相i2而非i1定义M3/M4终止事件。

## 电荷与换流

只计理想导通搬运电荷Qk时：

    ΔvC1=(Q1-Q2)/C1
    ΔvC2=(Q2-Q3)/C2

完整周期需加入换流电荷。M2和M5必须从各自真实节点网络写KCL；不能未经化简把它们都替换成共同单相LC模板。GaN反向导通子模态也需另设边界，不虚构硅体二极管。

## Numerical calibration

See `30_P25_NATIVE_METHOD_CALIBRATION.md`.  The P25-native local event chain
is feasible, and an event-periodic point can be found, but the present public
parameter set does not also reproduce nominal 0.5 MHz/equal 120-degree phase
spacing inside the published 5%-10% negative-current band.  This distinction
must be retained when using P25 as support for P24.

See `31_P25_INDUCTANCE_OPERATING_POINT_CLOSURE.md` for the independent
parameter-only check: P25 Eq. (20) and the direct current ramp both imply
about 32 nH at the printed 200 W/0.5 MHz/5% point, whereas Table III lists a
22 nH prototype inductor.

See `32_STRICT_JOINT_OPTIMIZATION.md` for the hard-gated joint feasibility
audit.  No tested branch passes every constraint.  A labelled negative-valley
correction plus phase-specific timing closes period, power and flying charge
balance, but still misses the fixed per-phase peak-current tolerance; it is a
diagnostic extension, not a P25 reproduction claim.
