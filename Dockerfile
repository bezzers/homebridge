FROM base-images.mgti-dal-so-art.mrshmc.com/poc/bionic1804:0.0.1
RUN apt-get update && apt-get install -y software-properties-common curl
RUN add-apt-repository ppa:deadsnakes/ppa && apt-get install -y python3.9
RUN apt-get install -y python3-distutils
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py
COPY . /opt/app-root/src
RUN cd /opt/app-root/src && pip3 install --no-cache-dir -r requirements.txt
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
WORKDIR /opt/app-root/src
CMD uvicorn api:app --port=8080 --host 0.0.0.0