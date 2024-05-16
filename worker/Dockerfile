FROM python:3.12-slim-bookworm

ENV WG_GATEWAY 172.20.0.50

RUN \
    # install iproute to change route
    apt-get update && apt-get install -y iproute2 curl \
    # install app's requirements
    && python3 -m pip install "humanfriendly==10.0.0" "requests==2.31.0" \
    # create entrypoint which changes the route to wireguard's IP
    && printf "#!/bin/bash\n\
ip route del default\n\
ip route add default via \${WG_GATEWAY}\n\
\n\
exec "\$@"\n\
" > /usr/bin/entrypoint \
    && chmod +x /usr/bin/entrypoint \
    && /bin/cat /usr/bin/entrypoint

COPY app.py /src/
WORKDIR /src

ENTRYPOINT ["/usr/bin/entrypoint"]
CMD ["python3", "app.py"]
