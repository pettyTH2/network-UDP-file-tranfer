import socket
import os
import struct
import hashlib
import random

CHUNK_SIZE = 1024
TIMEOUT = 2  # วินาที

# ---- CONFIG: ปรับค่าตรงนี้เพื่อทดลอง ----
DROP_EVERY = 10      # drop ทุก packet ที่หารลงตัวด้วย 10 (ตั้งเป็น 0 ถ้าไม่อยาก drop แบบ fixed)
DROP_PROB = 0.1      # ความน่าจะเป็นในการ drop packet (0.0 - 1.0)
CORRUPT_PROB = 0.1   # ความน่าจะเป็นในการ corrupt packet (0.0 - 1.0)
# -------------------------------------------

def compute_checksum(data: bytes) -> int:
    return int(hashlib.md5(data).hexdigest(), 16) % (1 << 16)

def make_packet(seq, data, eof):
    checksum = compute_checksum(data)
    header = struct.pack("!IHB", seq, checksum, eof)
    return header + data

def maybe_corrupt(data: bytes) -> bytes:
    if len(data) > 0:
        # สุ่มเลือก byte มาแก้ไข
        i = random.randint(0, len(data) - 1)
        corrupted_byte = (data[i] + 1) % 256
        data = data[:i] + bytes([corrupted_byte]) + data[i+1:]
    return data

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
                    # ---- Error Simulation ----
                    drop = False
                    corrupt = False

                    if DROP_EVERY > 0 and seq % DROP_EVERY == 0:
                        drop = True
                    elif random.random() < DROP_PROB:
                        drop = True

                    if not drop and random.random() < CORRUPT_PROB:
                        corrupt = True
                        packet = packet[:7] + maybe_corrupt(packet[7:])

                    if drop:
                        print(f"[X] Dropped seq {seq}")
                    else:
                        if corrupt:
                            print(f"[!] Corrupted seq {seq}")
                        else:
                            print(f"Sent seq {seq}")
                        sock.sendto(packet, client_addr)
                    # --------------------------

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
