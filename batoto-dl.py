from os.path import isfile, isdir
from os import name as OS_NAME, makedirs
from zlib import decompress as zlib_decompress, MAX_WBITS
from sys import exit, stdout
from re import findall, sub
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen, HTTPError
from zipfile import ZipFile, ZIP_DEFLATED


if OS_NAME == "nt":
    path_delim = "\\"
elif OS_NAME == "posix":
    path_delim = "/"


# Print [Batoto-dl] along with object
def __print__(s: str, _end: str ="\n") -> None:
    print("[Batoto-dl] {}".format(s), end=_end)
    stdout.flush()


# Get content of a url, decoding if encoded
def get_url_content(url: str):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        page_open = urlopen(req)
    except HTTPError as error:
        __print__(
            "Webpage({}) not found, Error code: {}"
            .format(url, error.code))
        return b""

    try:
        is_encoded = page_open.info()["Content-Encoding"]
    except:
        is_encoded = None

    if is_encoded == "gzip":
        return zlib_decompress(page_open.read(), 16 + MAX_WBITS)
    elif is_encoded is None:
        return page_open.read()
    else:
        print(is_encoded)
        exit(-1)


# Download chapter of manga from bato.to
def download_chapter(URL: str, is_cbz: bool=False) -> None:
    # Get url content and make soup
    page = get_url_content(URL)
    soup = BeautifulSoup(page, "html5lib")

    # Get title of the page
    t_title = soup.title.string

    # Get manga name from title
    title = t_title[:t_title.find("Vol.")]
    title = title[:title.find("Ch.")]
    
    # Remove invalid characters from title, for directory name
    title = sub("[:\\?/<>\+=]", "_", title)

    # If directory of that manga doesn't exist, make it
    if not isdir(title):
        makedirs(title)

    # Get chapter number from the title
    chapter_num = float(findall(r"[0-9.]+", t_title[t_title.find("Ch.") + 3:])[0])
    if (chapter_num.is_integer()):
        chapter_num = int(chapter_num)
    __print__("Downloading chapter: {}".format(str(chapter_num).zfill(3)), "\r")

    index = 1

    # Find all link of panel images
    imglist = \
        findall(
            (r"https://file-comic-2-2.anyacg.co/images/" +
                r"[0-9a-zA-Z]+/[0-9a-zA-Z]+/" +
                r"[0-9a-zA-Z_]+.[a-z]+").encode("utf-8"),
            page)

    path = "{}{}Chapter {}".format(
        title, path_delim, chapter_num)

    # If is_cbz is specified, make a cbz else make a directory
    if (is_cbz is True):
        if (isfile(path + ".cbz")):
            return
        zip = ZipFile(path + ".cbz", "w", ZIP_DEFLATED)
    else:
        path = path + path_delim
        if not isdir(path):
            makedirs(path)

    # Iterate over the 'link' list
    for i in imglist:
        # Filename according to storing preference
        if (is_cbz is True):
            filename = "{}.jpg".format(str(index).zfill(2))
        else:
            filename = "{}{}.jpg".format(path, str(index).zfill(2))

        __print__(
            "Downloading chapter: {} | slide: {}"
            .format(str(chapter_num).zfill(3), str(index).zfill(2)),
            "\r")

        if (isfile(filename) and is_cbz is False):
            index += 1
            continue

        # Get bytes of img from the link and
        # store either in cbz or as a file
        img = get_url_content(i.decode())
        if (is_cbz is True):
            zip.writestr(filename, img)
        else:
            file = open(filename, "wb")
            file.write(img)
            file.close()
        index += 1

    if (is_cbz is True):
        zip.close()

    return


# Download series from bato.to
def download_series(URL: str, is_cbz: bool=False) -> None:
    page = get_url_content(URL)
    soup = BeautifulSoup(page, "html5lib")
    
    title = soup.title.string
    
    t_hreflist = [a.get("href") for a in soup.find_all("a")]
    __print__("Manga: {}".format(title[:title.find("Manga")]))
    
    hreflist = []
    for i in t_hreflist:
        if isinstance(i, str) and "chapter" in i:
            hreflist.append("https://bato.to{}".format(i))

    hreflist = hreflist[::-1]
    for i in hreflist:
        download_chapter(i, is_cbz)


def main() -> None:
    parser = ArgumentParser(description="Download Manga from Bato.to URL")
    parser.add_argument("URL", help="URL to download manga from")
    parser.add_argument("-cbz", help="Save as cbz file", action="store_true")
    args = parser.parse_args()

    if not ("bato.to" in args.URL):
        __print__("Not a valid URL")

    try:
        if ("series" in args.URL):
            __print__("Possibly a series URL")
            download_series(args.URL, args.cbz)
        elif ("chapter" in args.URL):
            __print__("Possibly a chapter URL")
            download_chapter(args.URL, args.cbz)
    except KeyboardInterrupt:
        print("\nCTRL-C detected, exiting...")
        exit(-2)


if __name__ == "__main__":
    main()
