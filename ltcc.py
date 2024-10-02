from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import time

# Litecoin Core RPC yapılandırması
rpc_user = "ali"
rpc_password = "ali123"
rpc_port = "9332"
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:{rpc_port}")

def write_addresses_to_file(addresses, filename="ltcadresleri.txt"):
    try:
        with open(filename, "a") as file:
            for address in addresses:
                file.write(f"{address}\n")
                #print(address)
    except IOError as e:
        print(f"Dosyaya yazma hatası: {e}")

def fetch_transaction(txid, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return rpc_connection.getrawtransaction(txid, True)
        except JSONRPCException as e:
            if 'No such mempool transaction' in str(e):
                print(f"İşlem {txid} henüz indekslenmedi, {delay} saniye bekleniyor...")
                time.sleep(delay)
            else:
                raise
    print(f"İşlem {txid} hala bulunamadı, {retries} denemeden sonra.")
    return None

def print_addresses_in_transaction(txid):
    addresses = []
    raw_tx = fetch_transaction(txid)
    if raw_tx is None:
        addresses.append(f"Hata: {txid} işlemi bulunamadı.")
        write_addresses_to_file(addresses)
        return

    try:
        # Çıktıları ekrana bas
        for vout in raw_tx['vout']:
            if 'addresses' in vout['scriptPubKey']:
                for address in vout['scriptPubKey']['addresses']:
                    addresses.append(f"{address}")
                    #print(f"Çıktı Adresi: {address}")

        # Girişleri ekrana bas (detaylar eğer mevcutsa)
        for vin in raw_tx['vin']:
            if 'txid' in vin:
                prev_txid = vin['txid']
                vout_index = vin['vout']
                try:
                    prev_tx = fetch_transaction(prev_txid)
                    if prev_tx is None:
                        addresses.append(f"Girdi Adresi: {prev_txid} bulunamadı.")
                        continue
                    output = prev_tx['vout'][vout_index]
                    if 'addresses' in output['scriptPubKey']:
                        for address in output['scriptPubKey']['addresses']:
                            addresses.append(f"{address}")
                            #print(f"Girdi Adresi: {address}")
                except JSONRPCException:
                    addresses.append(f"Girdi Adresi: {prev_txid} bulunamadı.")
    except JSONRPCException as e:
        addresses.append(f"Hata: {e}")
    
    # Adresleri dosyaya yaz
    if addresses:  # Sadece adres varsa yaz
        write_addresses_to_file(addresses)

def print_addresses_in_block(block_number):
    try:
        # Blok hash'ini al
        block_hash = rpc_connection.getblockhash(block_number)
        # Blok detaylarını al
        block = rpc_connection.getblock(block_hash)
        #print(f"Blok Numarası: {block_number}, İşlem Sayısı: {len(block['tx'])}")
        for txid in block['tx']:
            print_addresses_in_transaction(txid)
    except JSONRPCException as e:
        addresses = [f"Hata: {e}"]
        write_addresses_to_file(addresses)
#blok numarasını yaz
def process_all_blocks(start_block=410000):
    latest_block = rpc_connection.getblockcount()
    for block_number in range(start_block, latest_block + 1):
        print(f"İşleniyor: Blok {block_number}")
        print_addresses_in_block(block_number)

# İşleme ilk bloktan başla
process_all_blocks()
