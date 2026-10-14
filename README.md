# CS224N 1246 作业（自学）

Stanford CS224N (Spring 2024) 四次作业的自学实现。

课程页面：https://web.stanford.edu/class/archive/cs/cs224n/cs224n.1246/

## 目录

| 目录 | 作业 | 内容 |
|---|---|---|
| `assignment1/` | A1 | 词向量：基于计数（SVD）与基于预测（GloVe） |
| `assignment2/` | A2 | 神经网络基础、张量求导、依存句法分析 |
| `assignment3/` | A3 | seq2seq + attention + subword 的神经机器翻译 |
| `assignment4/` | A4 | 自监督预训练与 Transformer 微调 |

期末项目（minBERT）在独立仓库 `cs224n-dfp`。

## 恢复数据

本仓库不含官方数据集（体积过大且可重新下载，已由 .gitignore 排除）：

    cd assignment2 && unzip -o a2.zip
    cd assignment3 && unzip -o a3_spr24_student_code.zip

## 环境

每个作业使用独立的 Python 环境，依赖见各目录下的 env.yml / local_env.yml / requirements.txt。
