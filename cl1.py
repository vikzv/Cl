from bs4 import BeautifulSoup
import requests
import json
import os

def get_soup(link):
    c = requests.session()
    r = c.get(link)
    return BeautifulSoup(r.text, 'html.parser')

def resize_image_url(url):
    # Mengganti _600x450.jpg menjadi _1200x900.jpg
    return url.replace("600x450.jpg", "1200x900.jpg")

def download_images(image_urls, folder_path):
    for i, url in enumerate(image_urls):
        image_filename = f"{i + 1:03d}.jpg"
        image_path = os.path.join(folder_path, image_filename)

        # Cek apakah file sudah ada, jika iya, lanjutkan dari posisi terakhir
        if os.path.exists(image_path):
            continue

        # Header untuk resume download
        headers = {'Range': 'bytes=0-'}

        with open(image_path, 'ab') as img_file:
            response = requests.get(url, headers=headers, stream=True)

            # Resume download dengan menambahkan ke file yang sudah ada
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    img_file.write(chunk)

def scrape_and_save_data(link):
    soup = get_soup(link)

    # Temukan elemen <script> dengan ID "ld_posting_data"
    script_element = soup.find('script', {'id': 'ld_posting_data'})

    # Dapatkan teks JSON dari kontennya
    json_text = script_element.contents[0]

    # Parse teks JSON
    json_data = json.loads(json_text)

    # Dapatkan informasi tambahan dari elemen HTML
    title = soup.find('span', {'id': 'titletextonly'}).text.strip().replace('"', '').replace('(', '').replace(')', '').replace('*', '').replace('!', '').replace('/', '').replace('-', '').replace(':', '').replace(',', '').replace('.', '')
    price_element = soup.find('span', {'class': 'price'})
    price = price_element.text.strip() if price_element else '(none)'
    
    # Dapatkan informasi kendaraan dari elemen HTML dengan kelas "attrgroup"
    attrgroup_element = soup.find_all('p', class_='attrgroup')
    vehicle_info = {}
    for attrgroup in attrgroup_element:
        for span in attrgroup.find_all('span'):
            key, *value_parts = span.get_text().split(':')
            value = ':'.join(value_parts).strip()
            vehicle_info[key.strip()] = value.strip()

    location_element = soup.find('span', {'class': 'price'}).find_next('span')
    location = location_element.text.strip() if location_element else '(none)'

    # Dapatkan deskripsi dari elemen HTML tanpa bagian QR Code Link to This Post
    description_element = soup.find('section', {'id': 'postingbody'})
    qr_code_label = description_element.find('p', {'class': 'print-qrcode-label'})
    if qr_code_label:
        qr_code_label.decompose()

    # Ambil teks deskripsi dari elemen
    description = description_element.get_text(strip=True, separator='\n')

    # Resize URL gambar
    image_urls = json_data.get('image', [])
    resized_urls = [resize_image_url(url) for url in image_urls]

    # Membuat objek JSON
    result_json = {
        'link': link,
        'title': title,
        'price': price,
        'vehicle_info': vehicle_info,
        'location': location.replace('(', 'In ').replace(')', ''),
        'Seller Description': description if description else '(none)'
    }

    # Membuat folder baru dengan nama title+lokasi
    folder_name = f"{price.replace('$', '').replace(',','')}_{title.replace(' ','')}"
    folder_path = os.path.join(os.getcwd(), folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # Menyimpan objek JSON ke file
    json_filename = f"{folder_name}.json"
    json_path = os.path.join(folder_path, json_filename)
    with open(json_path, 'w') as json_file:
        json.dump(result_json, json_file, indent=2)

    # Mengunduh gambar dengan resume download
    download_images(resized_urls, folder_path)

    print(f"Proses selesai. Data disimpan di {folder_path}")

if __name__ == "__main__":
    # Read links from a file named "links.txt"
    with open("i.txt", "r") as file:
        h = [line.strip() for line in file if line.strip()]

    # Process each link
    for link in h:
        scrape_and_save_data(link)
