FROM kalilinux/kali-rolling
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-scapy tcpreplay openssl dnsutils iputils-ping ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/redteam
CMD ["sleep", "infinity"]