FROM jupyter/pyspark-notebook:latest

USER root

# 1. Herramientas de Red, SSL y Entorno Gráfico
RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssl \
    curl \
    xvfb \
    fluxbox \
    x11vnc \
    supervisor \
    novnc \
    websockify \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Instalamos Brave Browser
RUN curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser-release.list \
    && apt-get update && apt-get install -y brave-browser

# 3. Librerias de Python para el kernel de Jupyter
USER jovyan
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "pymongo[srv]" dnspython certifi selenium webdriver-manager pandas \
    pyspark==3.5.0 scikit-learn matplotlib seaborn numpy

# 4. Conectores Spark-MongoDB
USER root
RUN wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.3.0/mongo-spark-connector_2.12-10.3.0.jar -P /usr/local/spark/jars/ \
    && wget https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-sync/4.11.1/mongodb-driver-sync-4.11.1.jar -P /usr/local/spark/jars/

# 5. CREACIÓN DEL SCRIPT DE ARRANQUE (Versión Blindada)
RUN cat <<EOF > /usr/local/bin/start-vnc.sh
#!/bin/bash
Xvfb :99 -screen 0 1280x1024x24 &
sleep 2
fluxbox &
x11vnc -display :99 -forever -nopw -listen localhost -xkb &
sleep 2
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen 6080
EOF

RUN chmod +x /usr/local/bin/start-vnc.sh

# 6. CONFIGURACIÓN DE SUPERVISOR (Incluyendo Jupyter)
RUN cat <<EOF > /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true
user=root

[program:desktop]
command=/bin/bash /usr/local/bin/start-vnc.sh
autorestart=true
priority=10

[program:jupyter]
command=start-notebook.sh --NotebookApp.token='' --NotebookApp.password=''
user=jovyan
directory=/home/jovyan/work
autorestart=true
priority=20
EOF
