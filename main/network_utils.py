import subprocess
import socket


def get_ifconfig_info():
    """
    ifconfig 명령어 실행 결과를 문자열로 반환하는 함수.
    Unix 계열에서 동작한다고 가정 (Windows라면 ipconfig로 변경 필요)
    """
    try:
        result = subprocess.check_output(["ifconfig"], stderr=subprocess.STDOUT)
        return result.decode("utf-8")
    except Exception as e:
        return f"ifconfig 실행 오류: {e}"


def convert_byte_order(value):
    """
    호스트 바이트 순서 -> 네트워크 바이트 순서 (htonl), 다시 ntohl로 변환해 예시를 보여줌
    value는 정수형으로 가정.
    """
    import struct

    network_order = socket.htonl(value)
    host_order = socket.ntohl(network_order)
    return f"원본: {value}, htonl: {network_order}, ntohl: {host_order}"


def convert_ip_address(ip_str):
    """
    IP 문자열을 바이너리로 변환(inet_pton), 다시 문자열(inet_ntop)로 변환
    IPv4 기준 예제
    """
    try:
        packed_ip = socket.inet_pton(socket.AF_INET, ip_str)
        unpacked_ip = socket.inet_ntop(socket.AF_INET, packed_ip)
        return f"입력 IP: {ip_str}, packed: {packed_ip}, unpacked: {unpacked_ip}"
    except socket.error as e:
        return f"IP 변환 오류: {e}"


def dns_lookup(domain):
    """
    도메인을 IP로 변환, IP를 도메인으로 다시 역변환하는 예제
    """
    try:
        ip = socket.gethostbyname(domain)
        reverse_domain = socket.gethostbyaddr(ip)[0]
        return f"도메인: {domain}, IP: {ip}, Reverse DNS: {reverse_domain}"
    except socket.error as e:
        return f"DNS 변환 오류: {e}"
