<img src="https://disc-wolido.oss-cn-beijing.aliyuncs.com/idm-logo/%E6%B5%85%E8%89%B2%E8%83%8C%E6%99%AFlogo-%E5%B7%A6%E5%8F%B3.png" style="height: 60px" />

- [中文](README_zh.md)
- [English](README.md)

---

# HEA DuckLake
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22075210.svg)](https://doi.org/10.5281/zenodo.22075210)

**六主元高熵合金（HEA）湖仓数据库。**

本项目提供面向高熵合金计算、机器学习训练与性能预测的基础数据集与工具链。数据以 **DuckDB/DuckLake 湖仓** 形式分发：整个数据集的实际总量为 **17.5 TB**，但您只需下载数十 MB 的元数据文件即可远程访问全部数据。

仓库内容包含：

- 湖仓元数据文件（`.ducklake`）及用于连接湖仓的 `init.sql` 文件。
- 用于生成描述符的 `calc_descriptors` 计算流程。
- 即开即用的 `predict_plasticity` 塑性分类预测模块。
- 完整可复现的笔记本级最小示例 `examples/minimal_workflow`。

## 目录

- [快速开始](#快速开始)
  - [在线体验（Binder）](#在线体验binder)
  - [本地复现](#本地复现)
- [什么是 HEA DuckLake？](#什么是-hea-ducklake)
- [访问湖仓](#访问湖仓)
  - [通过 DuckDB CLI](#通过-duckdb-cli)
  - [通过 Python](#通过-python)
- [示例与性能](#示例与性能)
- [数据计算架构](#数据计算架构)
- [最小可复现工作流](#最小可复现工作流)
- [塑性预测](#塑性预测)
- [注意事项](#注意事项)
- [相关工具](#相关工具)
- [引用](#引用)
- [许可协议](#许可协议)

## 快速开始

### 在线体验（Binder）

点击下方徽章即可在浏览器中直接运行示例 Notebook：

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Wolido/hea_ducklake/run_demo?urlpath=%2Fdoc%2Ftree%2Frun_demo%2Fmain.ipynb)

示例包含两个 Notebook：

- `main.ipynb` — 基础查询示例。
- `some_big_query.ipynb` — 耗时更长的查询示例。

> **注意：** `.ducklake` 格式的元数据不支持多个连接同时访问。运行 `some_big_query.ipynb` 前，请先关闭 `main.ipynb`，否则第三个单元格会报错。

### 本地复现

如果您想在自己的机器上复现整个集成框架，请使用 `examples/minimal_workflow`。这是完整流程的笔记本规模版本，几秒钟即可跑完：

1. **任务生成** — 将 HEA 组成任务推入 Redis 队列。
2. **分布式计算** — 无状态 Python 工作进程使用与完整流程相同的 `calc_descriptors/calc_py` 逻辑计算描述符。
3. **结果收集** — 将描述符汇总为 CSV 文件。
4. **湖仓存储** — 将 CSV 转换为压缩 Parquet 并上传至本地 MinIO（S3 兼容对象存储）。
5. **元数据目录** — 用一个小型 DuckDB 目录记录 Parquet 文件的 S3 位置。
6. **SQL 访问** — 通过元数据目录查询数据集，无需下载完整 Parquet 文件。

详细的步骤说明见下文 [最小可复现工作流](#最小可复现工作流)，或直接进入示例代码：

```bash
cd examples/minimal_workflow
pip install -r requirements.txt
docker compose up -d
python generate_tasks.py
python worker.py
python collect_results.py
python convert_to_parquet.py
python upload_to_minio.py
python create_metadata.py
python query_via_metadata.py
```

## 什么是 HEA DuckLake？

本项目开放两个湖仓：

- **`descriptor/`** — 六主元高熵合金描述符。
- **`pred_demo/`** — 机器学习预测结果。

以 `.ducklake` 结尾的文件为元数据文件。描述符湖仓包含：

| 表名 | 说明 |
|---|---|
| `hea_elements_6` | 元素组合表 |
| `hea_con_6` | 元素组成比例表 |
| `descriptor_names` | 描述符字段名称解释表 |
| `hea_6_c_x` | `hea_elements_6` 中索引为 `x` 的元素组合对应的描述符数据表 |

预测湖仓中的表名为 `pred_x`，其中 `x` 与描述符湖仓 `hea_elements_6` 中的组合索引对应。

## 访问湖仓

### 通过 DuckDB CLI

1. 从 [https://duckdb.org/install](https://duckdb.org/install) 安装 DuckDB 命令行客户端。
2. 安装 DuckLake 插件：`INSTALL ducklake;`
3. 在 `descriptor/` 目录下执行：

   ```bash
   duckdb --init init.sql
   ```

4. 使用 SQL 查询湖仓数据。

### 通过 Python

```bash
pip install duckdb
# 或使用项目提供的 pyproject.toml / uv.lock：
# uv sync
```

后续操作请参考 `use_descriptors.py` 脚本。

## 示例与性能

`descriptor/` 路径下的 `metadata.ducklake` 文件共引用 **5008 张表**，其中 **5005 张** 为六主元高熵合金描述符表。每张表有 **195 列**、超过 **1000 万行**，以压缩列存储格式保存，完整物化约需 4 GB 空间。

### 查询元素成分

在公网同城市环境下，查询可在 **2 秒内** 返回；跨城市约 **4 秒**；跨国或跨洲会更慢，但仍可接受。

<img src="./demo-pics/qc.png" style="height: 200px" />

### 查询部分列

得益于列存储，非全表查询无需传输全部数据。例如 `SELECT con_index, ave_fe1, rmse_ft2, range_fp5 FROM hea_6_c_128;` 返回 1000 万行 × 4 列数据，耗时约 **10 秒**。

<img src="./demo-pics/qd1.png" style="height: 200px" />

<img src="./demo-pics/qd2.png" style="height: 200px">

### 全库查询

`query_whole_db/` 目录下提供了用 Rust 实现的全库查询示例。在内网环境中，对总共 **500 亿组合** 的数据库全库查询仅需 **3 分 22 秒**（4 核 64 GB 虚拟机）。

<img src="./demo-pics/query_whole_db_2.png" style="height: 100px">

相同负载在 4 核 4 GB 虚拟机上每查询 100 个表重置一次连接，最终耗时 **7 分 38 秒**，说明全库查询可以在普通配置的机器上顺利完成。

<img src="demo-pics/query_4g.png" style="height: 100px">

### 边缘设备查询测试

我们还在 **4 GB 内存的树莓派 5** 上进行了查询测试：

<img src="demo-pics/raspi5.png" style="height: 200px">

- 单表整表查询会触发 OOM，因为压缩后的单表大小已超过树莓派内存。
- `SELECT * FROM hea_6_c_xxx LIMIT 100` 可在 **10 秒内** 完成。
- 上述列投影查询（4 列 1000 万行）仅需 **4 秒**。

<img src="demo-pics/raspi-100.png" style="height: 300px">

<img src="demo-pics/raspi-column.png" style="height: 400px">

## 数据计算架构

描述符计算流程位于 `calc_descriptors/` 目录下：

- Python 负责调度，将任务提交到 Redis 队列。
- 多个无状态工作进程从队列取任务并计算。
- 性能关键部分使用 Rust 实现，并通过 PyO3 封装为 Python 模块 `rs_calc_faster`。
- 每个工作进程在独立 Docker 容器中运行，且只使用一个 CPU 核心，因此扩容只需 `docker compose --scale`。
- 工作进程对中断信号做了处理：收到 `SIGINT` 后会先完成当前任务再退出。

由于 Redis 端口可暴露到外部，工作进程可以运行在任何地方（服务器、工作站、边缘设备），并支持运行时动态加入或离开集群。对于生产级的大规模众包计算，请参考 [IDM-GridCore](https://github.com/Wolido/idm-gridcore)。

## 最小可复现工作流

`examples/minimal_workflow` 是论文中集成框架的自包含、笔记本规模复现。它只使用第一个 6 元素家族并计算少量成分，几秒钟内即可完成。

### 它展示了什么

1. **无状态并行计算** — 任务被推入 Redis，由相同的工作进程处理。
2. **描述符计算** — 每个工作进程调用 `calc_descriptors/calc_py` 中的 `calc_main_progress()`。
3. **结果收集** — 描述符行被写入 `results.csv`。
4. **湖仓存储** — CSV 被转换为压缩 Parquet 并上传至 MinIO。
5. **元数据目录** — DuckDB 目录记录 Parquet 文件的 S3 位置。
6. **SQL 访问** — 通过目录查询数据集，无需下载完整对象。

### 前置要求

- Python 3.10+
- Rust 工具链及 `maturin`
- Docker / Docker Compose（或作为后备方案的 Homebrew MinIO）
- `examples/minimal_workflow/requirements.txt` 中列出的 Python 包

### 分步运行

```bash
# 1. 编译 Rust 扩展
cd calc_descriptors/calc_faster_rs
maturin develop --release

# 2. 安装示例依赖
cd ../../examples/minimal_workflow
pip install -r requirements.txt

# 3. 启动 Redis 和 MinIO
docker compose up -d

# 4. 生成任务并运行工作进程
python generate_tasks.py
python worker.py

# 5. 收集结果并转换为 Parquet
python collect_results.py
python convert_to_parquet.py

# 6. （可选）直接查询本地 Parquet
python query_parquet.py

# 7. 上传至 MinIO 并创建元数据目录
python upload_to_minio.py
python create_metadata.py

# 8. 通过元数据目录查询
python query_via_metadata.py
```

该示例支持通过环境变量配置所有端点、队列名和凭证。完整的环境变量列表及故障排除（包括 Docker Hub 不可达时通过 Homebrew 启动 MinIO 的方法）请参见 `examples/minimal_workflow/README.md`。

## 塑性预测

`predict_plasticity/` 目录包含一个可直接使用的塑性分类预测模块：

- `model_files/model.onnx` — 训练好的 ONNX 分类模型。
- `model_files/minmax_params.pkl` — Min-Max 归一化参数。
- `model_files/feature_names.json` — 模型所需的描述符列名。

该模块读取描述符 parquet 文件（如 `hea_6_c_*.parquet`），进行 Min-Max 归一化后通过 ONNX 模型推理，输出预测结果 parquet 文件。详细用法请参考 `predict_plasticity/README.md`。

## 注意事项

- 本项目的真实数据存储在与 S3 协议兼容的对象存储中。元数据类似于数据目录，可支持多用户同时访问。
- `init.sql` 中包含湖仓访问配置（例如 `s3_endpoint='idmlakehouse.tmslab.cn';`）。您也可以将其内容粘贴到 DuckDB CLI 中，或在 Python 中使用，效果相同。
- 若将元数据保存为 SQLite 格式并执行 `INSTALL sqlite`，多个用户可共享同一个元数据文件访问湖仓。
- 普通用户仅拥有**只读权限**，请勿尝试修改数据，不会成功。
- 若习惯用 Python 进行数据分析，建议使用 **Polars** 而非 Pandas。以上示例中的两表 JOIN 场景下，Polars 的惰性加载能显著节省内存并提高查询效率；Pandas 需要把整个表缓存到内存，4 GB 的压缩表在查询过程中可能消耗约 30 GB 内存。
- CPU 核心数并非越多越好。在我们的测试中，4~8 核是最佳甜点；过多核心会导致不必要的数据分割与传输，反而降低性能。全库查询 3 分 22 秒的成绩即来自一台 4 核 64 GB 虚拟机。
- `descriptor/` 路径下还提供了 `init-standalone.sql`，无需本地元数据即可连接湖仓。它直接通过 OSS 上的元数据文件 URL 访问，首次连接加载时间不到 10 秒，后续借助缓存机制速度与本地元数据方案相当。该方式还能避免元数据更新导致的版本不匹配问题。
- 我们也测试了使用 Postgres 保存元数据的方案：内网环境下速度良好，但公网环境下非常慢，推测是因为 Postgres 上的数据无法在本地缓存。
- 在 Docker 中运行 `que_push.py` 时，`docker-compose.yml` 里**千万不要**写 `restart: always` 或 `restart: unless-stopped`。否则所有任务计算完后容器会自动重启并开始第二轮计算。我和我的同事第一次运行时都踩过这个坑 😂。
- 我们已成功通过 [OpenClaw](https://openclaw.ai) 将项目链接交给 Agent，由其完成数据查询。

  <img src="demo-pics/try_openclaw.png" style="height: 300px">

## 相关工具

### AI Agent 技能

- **自然语言查询数据库：** [agent-hea6-ducklake](https://github.com/Wolido/agent-hea6-ducklake)
- **分布式计算部署：** [agent-idm-gridcore](https://github.com/Wolido/agent-idm-gridcore)

### 分布式计算框架

- **[IDM-GridCore](https://github.com/Wolido/idm-gridcore)** — 面向大规模描述符生成的众包并行计算框架。

## 引用

如果您在研究中使用了 HEA DuckLake，请引用（citation entry kept in original English）：

> Huang, X., Liu, Y., Shi, S. et al. HEA DuckLake: Metadata and Application Cases for a Trillion-Scale HEA Data Lakehouse (v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.22075211 (2026).

## 许可协议

<a rel="license" href="https://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a>
