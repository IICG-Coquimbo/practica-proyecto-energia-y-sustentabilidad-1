
FROM jupyter/pyspark-notebook:latest

USER root

# 1. Instalar dependencias base y configurar el repo de Google Chrome
RUN apt-get update && apt-get install -y wget gnupg2 curl && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# 2. Instalar Google Chrome y librerías de soporte
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    libnss3 \
    libgbm1 \
    libasound2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Instalar librerías de Python (incluyendo el manager de drivers)
RUN pip install selenium pymongo webdriver-manager pyspark==3.5.0


# Imagen base: trae Jupyter + Python + PySpark ya configurado

# Imagen base con Jupyter + PySpark (Spark 3.5.x)
 


FROM jupyter/pyspark-notebook:latest

USER root

# 1. Herramientas de Red, SSL y Entorno Gr fico (Xvfb para el scraper)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssl \
    curl \
    xvfb \
    fluxbox \
    x11vnc \
    supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/*



# Vuelve al usuario normal de Jupyter (buena pr ctica de seguridad)
 

# 2. Instalaci n de JARs: Versi n 10.3.0 (Compatible con Spark 3.5)
# Limpiamos la carpeta primero para que no queden versiones viejas chocando
RUN rm -f /usr/local/spark/jars/mongo-spark-connector* && \
    rm -f /usr/local/spark/jars/mongodb-driver* && \
    rm -f /usr/local/spark/jars/bson*

# 2. Instalamos Brave Browser (o Chromium) para el scraping
RUN curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser-release.list \
    && apt-get update && apt-get install -y brave-browser

 USER jovyan

# 3. Librer as de Python para todo el curso (Scraping + Atlas + Spark)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "pymongo[srv]" dnspython certifi selenium webdriver-manager pandas pyspark==3.5.0

# Forzamos usuario root para tener permisos de escritura
USER root

# 4. Conectores Spark-MongoDB
RUN wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.3.0/mongo-spark-connector_2.12-10.3.0.jar -P /usr/local/spark/jars/ \
    && wget https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-sync/4.11.1/mongodb-driver-sync-4.11.1.jar -P /usr/local/spark/jars/

# 5. Configuraci n de visualizaci n (noVNC)
COPY start-vnc.sh /usr/local/bin/start-vnc.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod +x /usr/local/bin/start-vnc.sh


RUN sed -i 's/\r$//' /usr/local/bin/start-vnc.sh \
    && chmod +x /usr/local/bin/start-vnc.sh && \
    chown -R jovyan:users /home/jovyan/work

# 6. Librerías de Python (Aquí recién cambiamos a jovyan)
USER jovyan
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "pymongo[srv]" dnspython certifi selenium webdriver-manager pandas pyspark==3.5.0

# 7. Configuración final y ejecución
USER root
ENV DISPLAY=:99
EXPOSE 8888 5900 6080 4040

# Solo un CMD al final
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]



