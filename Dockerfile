FROM python:3

RUN adduser --disabled-password --gecos '' streamlit
USER streamlit

WORKDIR /home/streamlit/app

COPY requirements.txt ./
COPY main.py ./
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT "8501"

CMD [ "/home/streamlit/.local/bin/streamlit", "run", "./main.py" ]