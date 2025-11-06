FROM nvidia/cuda:12.6.2-cudnn-devel-ubuntu24.04

# ロケール設定（日本語表示で文字化けしないように）
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# 作業ディレクトリの作成
WORKDIR /workspace

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    locales \
    git curl vim unzip \
 && locale-gen en_US.UTF-8 \
 && update-locale LANG=en_US.UTF-8 \
 && rm -rf /var/lib/apt/lists/*

# 仮想環境の作成
RUN python3 -m venv /opt/venv

# Pythonパッケージのインストール（PyTorch含む）
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install torch==2.7.1+cu126 --index-url https://download.pytorch.org/whl/cu126 && \
    /opt/venv/bin/pip install \
        numpy \
        pandas \
        matplotlib \
        scikit-learn \
        jupyterlab \
        seaborn \
        tqdm \
        ipywidgets \
        ipykernel

# Jupyter用カーネルの登録
RUN /opt/venv/bin/python -m ipykernel install --name xxx-dev --display-name "Python (xxx-dev)" --sys-prefix

# 起動時に仮想環境を有効化
RUN echo "source /opt/venv/bin/activate" >> /root/.bashrc

# コンテナ起動時のデフォルトコマンド
CMD ["bash"]
