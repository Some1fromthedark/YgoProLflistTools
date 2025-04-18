import argparse
import json
import os
import requests

def generate_card_line(card_id, card_name, status):
    line = f"{card_id} {status} "
    if len(line) < 20:
        line += " "*(20 - len(line))
    line += f"-- {card_name}\n"
    return line

def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("year", type=int)
    parser.add_argument("output_file")
    parser.add_argument("-p", "--preview", action="store_true", default=False)
    parser.add_argument("-t", "--lflist_tag", default=None)
    parser.add_argument("-a", "--add", action="append", nargs=2, type=int, metavar=("STRING", "INT"), default=[], help="Card ID and Status for the card to add")
    parser.add_argument("-r", "--remove", action="append", default=[])
    parser.add_argument("-b", "--ban", action="append", default=[])
    parser.add_argument("-l", "--limit", action="append", default=[])
    parser.add_argument("-s", "--semilimit", action="append", default=[])
    parser.add_argument("-f", "--lflist")
    
    args = parser.parse_args()
    
    cards_to_add = []
    cards_to_remove = []
    cards_to_ban = []
    cards_to_limit = []
    cards_to_semi = []
    
    year = args.year
    lflist_fn = args.output_file
    is_preview = args.preview
    lflist_tag = args.lflist_tag
    if lflist_tag is None:
        lflist_tag = f"JT {year}"
        if is_preview:
            lflist_tag += " PREVIEW"
    cards_to_add += args.add
    cards_to_remove += args.remove
    cards_to_ban += args.ban
    cards_to_limit += args.limit
    cards_to_semi += args.semilimit
    lflist_path = args.lflist
    
    with open(lflist_path, 'r') as f:
        lflist_content = f.read()
    lflist_lines = lflist_content.split("\n")

    status = 0
    status_lists = [cards_to_remove, cards_to_ban, cards_to_limit, cards_to_semi]
    for line in lflist_lines:
        line = line.strip()
        if len(line) == 0:
            status += 1
            if status == len(status_lists):
                break
        elif line[0] == '#':
            continue
        else:
            status_lists[status].append(line)
    
    cards_to_add_separate = [[], [], [], []]
    for card_id, status in cards_to_add:
        cards_to_add_separate[status].append(card_id)
    
    print("Year: {}, Preview: {}".format(year, is_preview))
    
    if is_preview:
        card_info_fn = "Data/CardInfo/{}_Preview.json".format(year)
    else:
        card_info_fn = "Data/CardInfo/{}.json".format(year)
    # Check if we have a cache for that year
    if os.path.exists(card_info_fn):
        print("Loading from cached data: {}".format(card_info_fn))
        # Read the data from the cache
        with open(card_info_fn, 'r') as f:
            card_info_json = json.load(f)
        card_info_data = card_info_json["data"]
    else:
        print("Requesting Data from db.ygoprodeck.com")
        # Query online database and cache results
        card_info_request = "https://db.ygoprodeck.com/api/v7/cardinfo.php?"
        if is_preview:
            start_date = "{}-1-1".format(year)
            card_info_request += "startdate={}&".format(start_date)
        end_date = "{}-12-31".format(year)
        card_info_request += "enddate={}".format(end_date)
        response = requests.get(card_info_request).json()
        with open(card_info_fn, 'w') as f:
            json.dump(response, f, indent=2)
        card_info_data = response["data"]
    
    content =   f"#[{lflist_tag}]\n" + \
                f"!{lflist_tag}\n" + \
                "$whitelist\n" + \
                "\n" + \
                "1 1                 -- Junior Journey Format\n" + \
                "\n" + \
                "# BANNED\n"
    for card_name in cards_to_ban:
        entry = next(filter(lambda x: x["name"] == card_name, card_info_data), None)
        if entry is not None:
            for image_entry in entry["card_images"]:
                line = generate_card_line(image_entry["id"], card_name, 0)
                content += line
        else:
            print(f"WARNING: Failed to find entry for {card_name}")
    for card_id in cards_to_add_separate[0]:
        line = generate_card_line(card_id, "????", 0)
        content += line
    content +=  "\n# LIMITED\n"
    for card_name in cards_to_limit:
        entry = next(filter(lambda x: x["name"] == card_name, card_info_data), None)
        if entry is not None:
            for image_entry in entry["card_images"]:
                line = generate_card_line(image_entry["id"], card_name, 1)
                content += line
        else:
            print(f"WARNING: Failed to find entry for {card_name}")
    for card_id in cards_to_add_separate[1]:
        line = generate_card_line(card_id, "????", 1)
        content += line
    content +=  "\n# SEMILIMITED\n"
    for card_name in cards_to_semi:
        entry = next(filter(lambda x: x["name"] == card_name, card_info_data), None)
        if entry is not None:
            for image_entry in entry["card_images"]:
                line = generate_card_line(image_entry["id"], card_name, 2)
                content += line
        else:
            print(f"WARNING: Failed to find entry for {card_name}")
    for card_id in cards_to_add_separate[2]:
        line = generate_card_line(card_id, "????", 2)
        content += line
    content +=  "\n# UNLIMITED\n"
    for entry in card_info_data:
        card_name = entry["name"]
        if card_name not in cards_to_remove and card_name not in cards_to_ban and card_name not in cards_to_limit and card_name not in cards_to_semi:
            for image_entry in entry["card_images"]:
                card_id = image_entry["id"]
                line = generate_card_line(card_id, card_name, 3)
                content += line
    for card_id in cards_to_add_separate[3]:
        line = generate_card_line(card_id, "????", 3)
        content += line
    with open(lflist_fn, 'w', encoding='utf-8') as f:
        f.write(content)
    
if __name__ == "__main__":
    main()