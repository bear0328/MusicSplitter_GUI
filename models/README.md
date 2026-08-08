# Bundled demucs checkpoints

丢这里 demucs 就不走网络直接用。install 脚本会硬链(Mac)/ 拷(Windows)进 `~/.cache/torch/hub/checkpoints/`。

## 含哪些文件

安装脚本期望这三个 `*.th` 文件名:

| 文件名 | 模型 | 大小 |
|---|---|---|
| `955717e8-8726e21a.th` | htdemucs (默认 4 轨) | 80 MB |
| `f7e0c4bc-ba3fe64a.th` | htdemucs_ft (4 轨 fine-tuned 集合,4 个签名) | 80 MB |
| `5c90dfd2-34c22ccb.th` | htdemucs_6s (6 轨乐器;**警告**:不是鼓件细分,名字误导) | 52 MB |

合计 ~213 MB。

## 怎么补

如果 `models/checkpoints/` 是空的,首次跑 demucs 会试图从 HuggingFace Hub 拉 `adefossez/HTDemucs`(safetensors 格式,走 `hf_xet`)。在 HF Hub CDN 不通的环境可能会卡死。手动补三种姿势:

### 1. 从本仓库 GitHub Release 下载(推荐,与仓库闭源同步)

仓库已把三个模型文件作为 [Release v0.1.0](https://github.com/bear0328/MusicSplitter_GUI/releases/tag/v0.1.0) 的 Asset,运行下载脚本即可:

```bash
python3 models/download_models.py
```

脚本会读取 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量;如果系统代理已开,通常能直接走。

### 2. 从 Meta 官方 AWS 拉

```bash
mkdir -p models/checkpoints
cd models/checkpoints
curl -L --progress-bar -O https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th
curl -L --progress-bar -O https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/f7e0c4bc-ba3fe64a.th
curl -L --progress-bar -O https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/5c90dfd2-34c22ccb.th
```

URL 列表参见 demucs 源码 `demucs/remote/files.txt`(也打进 wheel 了)。

### 3. 复用机器已有的 torch hub cache

```bash
ln ~/.cache/torch/hub/checkpoints/*.th models/checkpoints/
```

(同一 inode,本地一份磁盘占用 ≈ 0。)

### 4. 跳过这步,全靠网络

删掉这个目录,脚本会报警告但继续 —— 首次跑 demucs 自己拉,**先设置 `HF_TOKEN`** 否则 HuggingFace Hub 经常 403。

## 分发注意

- 走 zip / tar / 一并 git 时,注意 213 MB,git LFS 或 .gitignore:
  ```gitignore
  models/checkpoints/*.th
  !models/checkpoints/.gitkeep
  ```
- Windows 用户那边,因为没有管理员 mklink /H,install 脚本会 `copy` 出独立一份 → 213 MB 额外磁盘占用。

## 工作原理

demucs 4.x 加载模型是先查 HuggingFace Hub,失败回落到 legacy `dl.fbaipublicfiles.com`。legacy 路径用 `torch.hub.load_state_dict_from_url`,会先看 `~/.cache/torch/hub/checkpoints/<URL 文件名>` 存在就跳过下载。

GUI / install 脚本总在 demucs 调用时强制 `HF_HUB_OFFLINE=1`,强制走 legacy。所以这三份 .th 出现在用户 torch hub cache → demucs 直接命中,无需联网。
