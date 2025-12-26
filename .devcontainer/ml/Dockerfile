FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04

# ロケール設定（日本語表示で文字化けしないように）
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# 作業ディレクトリの作成
WORKDIR /workspace

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv python3-dev \
    locales git curl vim unzip tree \
 && locale-gen en_US.UTF-8 \
 && update-locale LANG=en_US.UTF-8 \
 && rm -rf /var/lib/apt/lists/*

# venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Pythonパッケージのインストール
RUN pip install --upgrade pip && \
    pip install torch==2.7.1+cu128 --index-url https://download.pytorch.org/whl/cu128 && \
    pip install \
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
RUN /opt/venv/bin/python -m ipykernel install --name ml-dev --display-name "Python (ml-dev)" --sys-prefix

# 起動時に仮想環境を有効化
RUN echo "source /opt/venv/bin/activate" >> /root/.bashrc

# プロジェクトのルートディレクトリをパスに追加
ENV PYTHONPATH="/workspace/ml"

# コンテナ起動時のデフォルトコマンド
CMD ["bash"]
