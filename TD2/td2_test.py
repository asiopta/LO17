from bs4 import BeautifulSoup
def extract_fichier(fichier_html, fichier_xml):
    '''extrait l'id du fichier'''
    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        f2.write("<fichier>") #ouvrir balise
        fichier = fichier_html.split("\\")[-1].split(".")[0]
        f2.write(fichier)
        f2.write("</fichier>\n")



def extract_title(fichier_html, fichier_xml):
    '''extrait le nom du fichier, le numero du bulletin et sa date'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    balise_title = soup.title.string.split(">")

    date = balise_title[0].split("/")
    fixed_date = date[2][:-1] + "/" + date[1] + "/" + date[0]


    titre = balise_title[2]
    num_bulletin = balise_title[1].split("\xa0")[1]

    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        f2.write("<numero>") #ouvrir balise
        f2.write(num_bulletin)
        f2.write("</numero>\n")

        f2.write("<date>") #ouvrir balise
        f2.write(fixed_date)
        f2.write("</date>\n")

        f2.write("<titre>") #ouvrir balise
        f2.write(titre)
        f2.write("</titre>\n")

def extract_author(fichier_html, fichier_xml):
    '''extrait l'auteur du fichier'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    meta_tag = soup.find("meta", attrs={"name": "author"})
    span_tags = soup.find_all("span", class_="style95")

    # Extract and print the content if found
    if meta_tag:
        #author = meta_tag.get("content")  # Get the value of the "content" attribute

        with open(fichier_xml, 'a', encoding="utf-8") as f2:
            for span in span_tags:
                content = span.get_text(separator=" ", strip=True)  # Extract clean text
                if(content != "" and "email" in content and "-" in content):
                    f2.write("<auteur>") #ouvrir balise
                    nom = content.split("-")[1] + "-" + content.split("-")[2]
                    f2.write(nom)
                    f2.write("</auteur>\n")

            
def extract_text(fichier_html, fichier_xml):
    '''extrait le texte du fichier'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    span_tags = soup.find_all("span", class_="style95")
    texte = ""
    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        # Iterate through each <span> and extract text separately
        for i, span in enumerate(span_tags):
            for content in span.stripped_strings:
                if(content != ""):
                    if(content[-1] == "."):
                        texte = texte + " " + content
        f2.write("<texte>") #ouvrir balise
        f2.write(texte)
        f2.write("</texte>\n")


def extract_rubrique(fichier_html, fichier_xml):
    '''extrait le texte du fichier'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    span_tags = soup.find_all("span", class_="style42")

    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        # Iterate through each <span> and extract text separately
        for i, span in enumerate(span_tags):
            for content in span.stripped_strings:
                    if( "/" not in content):
                        f2.write("<rubrique>") #ouvrir balise
                        f2.write(content)
                        f2.write("</rubrique>\n")
                    

def extract_images_legends(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    images_info = []
    
    for div in soup.find_all("div", style="text-align: center"):
        img_tag = div.find("img")
        span_tag = div.find("span", class_="style21")
        
        if img_tag and span_tag:
            img_url = img_tag["src"]
            legende = span_tag.get_text(strip=True)
            images_info.append((img_url, legende))
    return images_info


def write_image_infos(fichier_html, fichier_xml):
    img_infos = extract_images_legends(fichier_html)
    #extract images using .jpg  67940
    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        if img_infos:
            f2.write("<images>\n")
            # Extract and print the 'src' attribute of each image
            for (img_src, img_legende) in img_infos:
                f2.write("<image>\n")
                f2.write("<urlImage>")
                f2.write(img_src)
                f2.write("</urlImage>\n")
                    
                f2.write("<legendeImage>")
                #print(img_caption)
                f2.write(img_legende)
                f2.write("</legendeImage>\n")
                f2.write("</image>\n")
            f2.write("</images>\n")


def extract_contacts(fichier_html, fichier_xml):
    '''Extracts text from spans without links to "67391.htm"'''
    # Open and parse the HTML file
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Find all <span> tags with class "style85"
    span_tags = soup.find_all("span", class_="style85")

    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        # Iterate through each <span> tag
        for span in span_tags:
            content = span.get_text(separator=" ", strip=True)  # Extract clean text
            if("-" in content):
                #print(content)  # Debugging output
                f2.write("<contact>")  # Open tag
                f2.write(content)  # Write extracted text
                f2.write("</contact>\n")  # Close tag


#for every individual bulletin
def extract_file(fichier_html, fichier_xml):
    with open(fichier_xml, "a", encoding="utf-8") as f:
        f.write("<bulletin>\n")
    extract_fichier(fichier_html, fichier_xml)
    extract_title(fichier_html, fichier_xml)
    extract_rubrique(fichier_html, fichier_xml)
    extract_author(fichier_html, fichier_xml)
    extract_text(fichier_html, fichier_xml)
    write_image_infos(fichier_html, fichier_xml)
    extract_contacts(fichier_html, fichier_xml)
    with open(fichier_xml, "a", encoding="utf-8") as f:
        f.write("</bulletin>\n")




# for all rubriques
from pathlib import Path
def extract_all_files(directory, fichier_xml):
    with open(fichier_xml, "w", encoding="utf-8") as f:
        f.write("<corpus>\n")
    
    dir_path = Path(directory)
    
    if not dir_path.is_dir():
        print("Invalid directory path")
        return
    
    #for each htm file in the repository 
    for file in dir_path.iterdir():  # Iterate through directory contents
        if file.is_file():  # Ensure it's a file
            file_name = str(file.resolve())  # Print full absolute path
        extract_file(fichier_html= file_name, fichier_xml= fichier_xml)

    with open(fichier_xml, "a", encoding="utf-8") as f:
        f.write("</corpus>\n")


if __name__ == "__main__":
    extract_all_files("BULLETINS", "corpus.XML")

