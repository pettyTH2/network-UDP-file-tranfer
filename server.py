import socket
import os
import struct
import hashlib
import time

CHUNK_SIZE = 1024
TIMEOUT = 2  # วินาที

def compute_checksum(data: bytes) -> int:
    return int(hashlib.md5(data).hexdigest(), 16) % (1 << 16)

def make_packet(seq, data, eof):
    checksum = compute_checksum(data)
    header = struct.pack("!IHB", seq, checksum, eof)
    return header + data

def main():
    server_ip = "127.0.0.1"
    server_port = 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, server_port))
    print(f"Server listening on {server_ip}:{server_port}")

    while True:
        data, client_addr = sock.recvfrom(1024)
        filename = data.decode().strip()
        print(f"Client {client_addr} requested file: {filename}")

        if not os.path.exists(filename):
            sock.sendto(b"ERROR: File not found", client_addr)
            continue

        with open(filename, "rb") as f:
            seq = 0
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    packet = make_packet(seq, b"", 1)  # EOF
                    sock.sendto(packet, client_addr)
                    print("File transfer complete.")
                    break

                packet = make_packet(seq, chunk, 0)

                while True:
                    sock.sendto(packet, client_addr)
                    print(f"Sent seq {seq}, waiting for ACK...")

                    sock.settimeout(TIMEOUT)
                    try:
                        ack, _ = sock.recvfrom(1024)
                        ack_seq = int(ack.decode())
                        if ack_seq == seq:
                            print(f"ACK {ack_seq} received")
                            break
                    except socket.timeout:
                        print(f"Timeout, resending seq {seq}")

                seq += 1

if __name__ == "__main__":
    main()
