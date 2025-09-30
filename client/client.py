import socket
import struct
import hashlib

CHUNK_SIZE = 1024

def compute_checksum(data: bytes) -> int:
    return int(hashlib.md5(data).hexdigest(), 16) % (1 << 16)

def parse_packet(packet: bytes):
    header = packet[:7]  # Seq (4B), Checksum (2B), EOF (1B)
    data = packet[7:]
    seq, checksum, eof = struct.unpack("!IHB", header)
    return seq, checksum, eof, data

def main():
    server_ip = "127.0.0.1"
    server_port = 5000
    filename = "test.txt"
    output_file = "received_" + filename

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ส่ง request
    sock.sendto(filename.encode(), (server_ip, server_port))

    expected_seq = 0
    with open(output_file, "wb") as f:
        while True:
            packet, _ = sock.recvfrom(1500)
            seq, checksum, eof, data = parse_packet(packet)

            if compute_checksum(data) != checksum:
                print(f"Packet {seq} corrupted, discard.")
                continue

            if seq == expected_seq:
                print(f"Received seq {seq}")
                f.write(data)
                sock.sendto(str(seq).encode(), (server_ip, server_port))
                expected_seq += 1
            else:
                print(f"Unexpected seq {seq}, expected {expected_seq}")
                # ส่ง ACK ล่าสุดกลับไป
                sock.sendto(str(expected_seq - 1).encode(), (server_ip, server_port))

            if eof == 1:
                print("End of file received.")
                break

if __name__ == "__main__":
    main()
