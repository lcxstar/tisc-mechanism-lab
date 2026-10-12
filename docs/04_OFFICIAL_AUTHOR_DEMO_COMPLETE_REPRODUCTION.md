# TISC 原作者示例模型复现与保存记录（2026-10-12）

## 任务边界

停止准噶尔盆地 300–0 Ma 演化模型的地质参数校准与排水修正；只对原作者提供的 TISC 示例完成原始输入、原运行范围、数值结果和诊断的可重复复现。

**代码版本** Daniel García-Castellanos 的 danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd。原始示例来自 tisc/demo/README 和 tisc/demo/run_all.sh。

**两个不同源码标准**  
A. normalized_upstream 仅将源码的两处非断行空格归一化以使 GNU 编译器正常编译，没有物理/排水算法修改。  
B. audited_03t_optimized 明确包含已审计的湖泊加速、蒸发缓存、03k 负斜率处理以及 03s/03t 沉积质量账本观测与打印修正。**不是完全未修改的原版求解器**，不可将其结果表述为 bitwise-identical original。

所有输入 PRM、ZINI、UNIT、SLV、INT、REC、RIV 等均按 SHA256 完整保留。运行只有静音绘图、增加诊断级别的命令行覆盖，不改变作者的初始地形、地质时长、网格、构造、气候和沉积参数。验收首先检查退出码为 0、输出原生 .xyw 网格数量正确、输入 SHA256 不变。**数值跑通并不等于作者历史结果精确重现或真实地质解释正确**。

## 原始案例复现

| 原作者示例 | 原始规模与时间 | 代码版本 | 实际结果 |
|---|---|---|---|
| 1、2 外部挠曲计算 | 11/51 网格，中心挠曲 675.1/711.0m | A | [静态基准验收](https://github.com/lcxstar/tisc-mechanism-lab/actions/workflows/01_official_flexure.yml) |
| 3_flexure | 原始 flex.PRM / 3 单元 | A | 已完成原始静态项目模型 |
| 4_river_transport | 101×101，0–20 Myr | B | [已计算并保存](../results/04_09_official_demo_suite/04_river/) |
| 5_lakes / 1lake | 51×51，0–0.5 Myr | A | [已计算并保存](../results/04_09_official_demo_suite/05_lake_one/) |
| 5_lakes / 2lakes | 81×81，0–1 Myr | A | [已计算并保存](../results/04_09_official_demo_suite/05_lakes_two/) |
| 6_tectonics | 401×401，0–15 Myr | B | [03t 验证](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165304319) 和 [03v 双版本控制](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178743124)；本轮再次独立复核 |
| 7_climate | 101×101，0–5 Myr | B | [已计算并保存](../results/04_09_official_demo_suite/07_climate/) |
| 8_Ebro_evol | 208×110，−60–0 Myr | B | **运行完成但历史结果不一致** [结果和原生输出](../results/04_09_official_demo_suite/08_ebro/) |
| 9_Iberian_drainage | 159×141，0–0.1 Myr | A | [已计算并保存](../results/04_09_official_demo_suite/09_iberia/) |

各案例独立保存 RUN_QC.json、SOURCE_AND_INPUTS.json、SOURCE_PATCH_AUDIT、包含原始输入和 .xyw/.xyzt/.hrz/.bas/.lak/RUN.log 的压缩模型归档及 SHA256。完成/失败都不删除，不只使用可能到期的 GitHub Actions 附件。

## 埃布罗盆地真实数值复现审计：2016 参考差异明确存在

原作者提交了一个 TISC_2016-08-30 运行的 [Ebro_evol.screen](https://github.com/danigeos/tisc/blob/d18b7d270f4d671b80223e10dede329ad35cafdd/tisc/demo/8_Ebro_evol/Ebro_evol.screen)。

本轮原作者所附现行输入完整运行了 −60 至 0 Ma，进程正常退出并保存全部 22,880 个输出节点，但对照该历史屏幕日志，在 121 个相同年龄中，120 个地表指标可比较的记录发现：

- 历史日志与新运行的模型地形最大值 RMS 差约 2341 m，单时刻最大差约 7871 m。
- 打印的累积沉积体积 RMS 差约 49006 km³。
- 模拟开始 −59.5 Ma，2016 作者最大地形高程 1200.8 m，而当前源码加速版本计算 9071.6 m。
- 使用现行源代码的 **纯 A 编译版本**、保持作者物理输入不变、独立计算初始 0.5 Myr 后，仍得到 9071.6 m。这说明该早期差异 **不是 03t 加速补丁单独造成**。
- 但 2016 源码/输入环境与 2026 存档版本的完整差异尚未独立确认，不能把这种不一致具体归因于某个唯一错误。

详见 [逐阶段比较](../results/04_09_official_demo_suite/08_ebro/reference_compare/EBRO_AUTHOR_SCREEN_COMPARISON.md) 与 [纯原版初期程序复核](../results/04_09_official_demo_suite/08_ebro/pristine_early/EARLY_SOURCE_GEOLOGY_ISOLATION.json)。

**因此 Ebro 应明确标注为 EXECUTION_PASS / HISTORICAL_NUMERIC_MATCH_FAIL**，不应误称已重现 2003 年论文所有地质场。这是这次复现最有意义的质量检查之一。

## 数值与地质验收分开

- 03y 全域坡度容差否定性结果保留，03z 微湖泊出口敏感性、03aa 镜像唯一低出口是额外的机制实验，**并不是**官方 5_lakes 复现的替代。
- 03t 纠正了浮点总质量打印差异，但不会自然改善数值长期敏感性、盆地沉积中心和古高程的可信度。
- 准噶尔模型暂停，仅作为已有机制参考，不向作者示例注入准噶尔几何或额外地质输入。
