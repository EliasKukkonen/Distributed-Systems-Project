# Käytetään kevyttä Python-kuvaa
FROM python:3.9-slim

# Asetetaan työskentelykansio
WORKDIR /app

# Määritellään ympäristömuuttuja niin, että Python etsii moduulit myös proto-kansiosta
ENV PYTHONPATH="/app/proto"

# Kopioidaan riippuvuusmääritystiedosto ja asennetaan riippuvuudet
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopioidaan koko projektin sisältö konttiin
COPY . .

# Käynnistetään palvelin
CMD ["python", "server.py"]
