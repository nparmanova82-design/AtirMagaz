"""Demo katalog: brendlar, notalar, atirlar, hajmlar, sharhlar, promokodlar va admin.

    python manage.py seed_atir          # bo'sh bazani to'ldiradi
    python manage.py seed_atir --reset  # katalogni o'chirib, qaytadan yaratadi
"""
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from orders.models import PromoCode
from shop.models import Brand, Note, Perfume, Review, Variant

BRANDS = [
    # nomi, mamlakat, yil, nish, tavsif
    ("Chanel", "Fransiya", 1910, False,
     "Koko Shanel asos solgan afsonaviy moda uyi. N°5 bilan parfyumeriya tarixini o'zgartirgan brend."),
    ("Dior", "Fransiya", 1946, False,
     "Kristian Dior uyi — nafis frantsuz klassikasi va zamonaviy xitlar: J'adore, Sauvage, Miss Dior."),
    ("Yves Saint Laurent", "Fransiya", 1961, False,
     "Jasur va zamonaviy fransuz brendi. Libre, Black Opium va Y — butun avlodning sevimli hidlari."),
    ("Tom Ford", "AQSh", 2006, False,
     "Tom Ford Private Blend kolleksiyasi — hashamatli, quyuq va esda qolarli kompozitsiyalar."),
    ("Giorgio Armani", "Italiya", 1975, False,
     "Italyancha nafosat: Acqua di Giò va Sì kabi zamonaviy klassikalar."),
    ("Lancôme", "Fransiya", 1935, False,
     "Fransuz go'zallik uyi. La Vie Est Belle — dunyodagi eng mashhur ayollar atirlaridan biri."),
    ("Versace", "Italiya", 1978, False,
     "Yorqin, jo'shqin va o'ziga ishongan italyan uslubi."),
    ("Paco Rabanne", "Ispaniya", 1966, False,
     "Futuristik dizayn va o'yinqaroq hidlar. 1 Million — erkaklar atirlarining ikonasi."),
    ("Carolina Herrera", "AQSh", 1988, False,
     "Nyu-Yorkcha nafosat. Good Girl va Bad Boy flakonlari o'zi bir san'at asari."),
    ("Gucci", "Italiya", 1921, False,
     "Florensiyalik moda uyi — romantik va zamonaviy gul kompozitsiyalari."),
    ("Dolce & Gabbana", "Italiya", 1985, False,
     "O'rta yer dengizi quyoshi va yengilligi — Light Blue seriyasi."),
    ("Creed", "Fransiya", 1760, True,
     "Olti avlod davomida qo'lda tayyorlanadigan atirlar. Aventus — nish parfyumeriyaning qiroli."),
    ("Maison Francis Kurkdjian", "Fransiya", 2009, True,
     "Frensis Kurkdjyan — zamonamizning eng mashhur parfyumeri. Baccarat Rouge 540 uning imzosi."),
    ("Kilian Paris", "Fransiya", 2007, True,
     "Kilian Xennessi yaratgan hashamatli uy: likyor, shirinlik va gullarning jasur uyg'unligi."),
    ("Byredo", "Shvetsiya", 2006, True,
     "Skandinaviya minimalizmi va xotiralar haqida hikoya qiluvchi hidlar."),
    ("Le Labo", "AQSh", 2006, True,
     "Nyu-Yorklik laboratoriya-brend: har bir flakon buyurtma paytida qo'lda to'ldiriladi."),
    ("Initio", "Fransiya", 2015, True,
     "Parfyumeriyaning hissiyotga ta'sirini o'rganuvchi nish uy. Ud va mushkning ustasi."),
    ("Montale", "Fransiya", 2003, True,
     "Parijlik nish brend — sharqona ud, atirgul va qahva kompozitsiyalari."),
    ("Amouage", "Ummon", 1983, True,
     "Ummon sultonligining hashamatli parfyumeriya uyi. Ladan va ud — uning ruhi."),
    ("Jo Malone London", "Buyuk Britaniya", 1990, False,
     "Britaniyacha soddalik: kolonyalarni bir-biri bilan qatlamlab sepish an'anasi."),
    ("Lattafa", "BAA", 1980, False,
     "Dubaylik brend — sharqona uslubdagi sifatli va hamyonbop atirlar."),
]

# brend, nomi, jins, konsentratsiya, oila, yil, parfyumer, rang, shakl, qopqoq,
# 100 ml narxi, (top, heart, base), fasl, vaqt, turg'unlik, shleyf, belgilar, tavsif
PERFUMES = [
    ("Chanel", "Coco Mademoiselle", "women", "edp", "chypre", 2001, "Jacques Polge",
     "#F0B9A6", "classic", "gold", 2_950_000,
     (["Apelsin", "Bergamot", "Greypfrut"], ["Atirgul", "Yasmin", "Lichi"],
      ["Pachuli", "Vetiver", "Vanil", "Oq mushk"]),
     "all", "any", 4, 4, {"bestseller"},
     "Erkin va jasur ayol uchun zamonaviy shipr. Sitrusli tazelik atirgul va yasmin yuragiga, "
     "so'ng iliq pachuli va vanilga o'tadi. Kundalik hayotda ham, kechki tadbirda ham o'rinli."),
    ("Chanel", "N°5", "women", "edp", "floral", 1921, "Ernest Beaux",
     "#E8D19A", "classic", "gold", 3_100_000,
     (["Aldegidlar", "Ilang-ilang", "Neroli", "Bergamot"], ["Iris", "Yasmin", "Atirgul", "Marvaridgul"],
      ["Sandal", "Vanil", "Anbar", "Mushk", "Vetiver"]),
     "cold", "evening", 5, 4, set(),
     "Bir asrdan ortiq vaqtdan beri nafosat ramzi. Aldegidli gul guldastasi — "
     "klassika, u hech qachon modadan qolmaydi."),
    ("Chanel", "Chance Eau Tendre", "women", "edt", "floral", 2010, "Jacques Polge",
     "#F6C9D2", "round", "silver", 2_450_000,
     (["Behi", "Greypfrut"], ["Sumbul", "Yasmin"], ["Oq mushk", "Iris", "Anbar", "Kedr"]),
     "warm", "day", 3, 3, set(),
     "Yumshoq, mevali-gulli va juda nozik. Bahor kunlari va ofis uchun ideal tanlov."),
    ("Dior", "J'adore", "women", "edp", "floral", 1999, "Calice Becker",
     "#E9C46A", "tall", "gold", 2_650_000,
     (["Nok", "Qovun", "Mandarin", "Bergamot"], ["Yasmin", "Atirgul", "Tuberoza", "Orxideya"],
      ["Mushk", "Vanil", "Kedr"]),
     "all", "any", 4, 4, {"bestseller"},
     "Oltin rangli gul guldastasi — ayollik va nafosatning ramzi. Yasmin va tuberoza "
     "terida uzoq vaqt yorqin saqlanadi."),
    ("Dior", "Miss Dior", "women", "edp", "floral", 2021, "François Demachy",
     "#F4B6C2", "round", "silver", 2_480_000,
     (["Marvaridgul", "Pion", "Iris"], ["Atirgul"], ["Vanil", "Mushk", "Tonka loviya"]),
     "warm", "day", 3, 3, {"new"},
     "Sevgi haqidagi gulli hikoya: pion, marvaridgul va atirguldan to'qilgan guldasta."),
    ("Yves Saint Laurent", "Libre", "women", "edp", "floral", 2019, "Anne Flipo, Carlos Benaïm",
     "#D9A441", "square", "gold", 2_350_000,
     (["Lavanda", "Mandarin", "Qora smorodina"], ["Lavanda", "Apelsin guli", "Yasmin"],
      ["Vanil", "Mushk", "Kedr", "Ambra"]),
     "all", "any", 5, 4, {"bestseller"},
     "Erkinlik atiri: erkaklar lavandasi va ayollar apelsin guli uchrashgan jasur kompozitsiya."),
    ("Yves Saint Laurent", "Black Opium", "women", "edp", "gourmand", 2014, "Nathalie Lorson, Marie Salamagne",
     "#3A2A3F", "tall", "black", 2_200_000,
     (["Nok", "Pushti qalampir", "Apelsin guli"], ["Qahva", "Yasmin", "Achchiq bodom", "Qizilmiya"],
      ["Vanil", "Pachuli", "Kedr", "Kashmeran"]),
     "cold", "evening", 5, 5, {"bestseller"},
     "Qora qahva va oq gullarning energiyasi. Kechki uchrashuvlar uchun yaratilgan jozibali gurmand."),
    ("Lancôme", "La Vie Est Belle", "women", "edp", "gourmand", 2012,
     "Olivier Polge, Dominique Ropion, Anne Flipo",
     "#E8A9B8", "facet", "silver", 2_150_000,
     (["Qora smorodina", "Nok"], ["Iris", "Yasmin", "Apelsin guli"],
      ["Pralin", "Vanil", "Pachuli", "Tonka loviya"]),
     "cold", "any", 5, 5, {"bestseller"},
     "«Hayot go'zal» — shirin pralin va iris tabassumi. Dunyodagi eng ko'p sotiladigan atirlardan biri."),
    ("Carolina Herrera", "Good Girl", "women", "edp", "oriental", 2016, "Louise Turner",
     "#1F2A44", "tall", "gold", 2_050_000,
     (["Bodom", "Qahva", "Bergamot", "Limon"], ["Tuberoza", "Yasmin", "Apelsin guli", "Atirgul"],
      ["Tonka loviya", "Kakao", "Vanil", "Pralin", "Sandal"]),
     "cold", "evening", 4, 4, set(),
     "Yaxshi qizning yorqin va yomon qizning qorong'i tomoni. Poshna shaklidagi flakon — ikona."),
    ("Giorgio Armani", "Sì", "women", "edp", "chypre", 2013, "Christine Nagel",
     "#C9A27E", "classic", "black", 1_950_000,
     (["Qora smorodina"], ["Atirgul", "Freziya"], ["Vanil", "Pachuli", "Yog'och notalari"]),
     "all", "any", 4, 3, set(),
     "«Ha» deyishga jur'at qiluvchi ayol uchun. Qora smorodina nektari va iliq vanilli shipr."),
    ("Gucci", "Bloom", "women", "edp", "floral", 2017, "Alberto Morillas",
     "#E8A0AE", "round", "gold", 1_850_000,
     (["Tuberoza"], ["Yasmin"], ["Rangun liana"]),
     "warm", "day", 3, 3, set(),
     "Gullab-yashnayotgan bog' — tuberoza va yasmin. Romantik, nozik va ayolona."),
    ("Versace", "Bright Crystal", "women", "edt", "floral", 2006, "Alberto Morillas",
     "#F6C6D0", "facet", "silver", 1_250_000,
     (["Yuzu", "Anor"], ["Pion", "Magnoliya", "Lotus"], ["Mushk", "Qizil daraxt", "Anbar"]),
     "warm", "day", 3, 2, set(),
     "Muzdek yangi anor va pion — issiq yoz kunlari uchun yorqin, yengil hid."),
    ("Kilian Paris", "Love, Don't Be Shy", "women", "edp", "gourmand", 2007, "Calice Becker",
     "#F3A6B8", "square", "black", 4_400_000,
     (["Neroli", "Pushti qalampir", "Bergamot"], ["Apelsin guli", "Shilvi", "Yasmin", "Atirgul"],
      ["Zefir", "Vanil", "Karamel", "Mushk"]),
     "cold", "evening", 5, 4, set(),
     "Zefir va apelsin gulidan yaratilgan shirin vasvasa. Nish gurmandlarning eng mashhuri."),
    ("Lattafa", "Yara", "women", "edp", "gourmand", 2020, "",
     "#F7C6D9", "round", "gold", 420_000,
     (["Orxideya", "Geliotrop", "Mandarin"], ["Tropik mevalar"], ["Vanil", "Mushk", "Sandal"]),
     "all", "any", 4, 4, {"bestseller"},
     "Pushti bulutdek yumshoq va shirin. Hamyonbop narxda hashamatli hid — ijtimoiy tarmoqlar xiti."),
    ("Jo Malone London", "English Pear & Freesia", "women", "edc", "floral", 2010, "Christine Nagel",
     "#E6D58A", "classic", "silver", 1_750_000,
     (["Nok", "Qovun"], ["Freziya", "Atirgul"], ["Pachuli", "Ravoch", "Anbar", "Mushk"]),
     "warm", "day", 2, 2, set(),
     "Kuzgi bog'dagi pishgan nok va oq freziya. Boshqa Jo Malone hidlari bilan qatlamlashga mos."),

    # — Erkaklar —
    ("Dior", "Sauvage", "men", "edt", "fougere", 2015, "François Demachy",
     "#3B5B7A", "square", "black", 2_250_000,
     (["Bergamot", "Qalampir"], ["Lavanda", "Pushti qalampir", "Vetiver", "Pachuli", "Geran", "Elemi"],
      ["Ambroksan", "Kedr", "Labdanum"]),
     "all", "any", 4, 5, {"bestseller"},
     "Yovvoyi tabiat va ochiq osmon. Bergamot tazeligi va ambroksan izi — "
     "so'nggi o'n yillikning eng mashhur erkaklar atiri."),
    ("Chanel", "Bleu de Chanel", "men", "edp", "woody", 2014, "Jacques Polge",
     "#1E2A3A", "square", "black", 2_750_000,
     (["Greypfrut", "Limon", "Yalpiz", "Pushti qalampir"], ["Zanjabil", "Muskat yong'og'i", "Yasmin"],
      ["Ladan", "Vetiver", "Kedr", "Sandal", "Pachuli"]),
     "all", "any", 4, 4, {"bestseller"},
     "Erkinlik va o'ziga ishonch timsoli. Sitrus va ladanning nafis uyg'unligi — har qanday vaziyatga mos."),
    ("Paco Rabanne", "1 Million", "men", "edt", "oriental", 2008, "Christophe Raynaud, Olivier Pescheux",
     "#D4A537", "square", "gold", 1_550_000,
     (["Greypfrut", "Yalpiz", "Qizil mandarin"], ["Atirgul", "Doljin"], ["Teri", "Anbar", "Pachuli"]),
     "cold", "evening", 4, 5, set(),
     "Oltin quyma shaklidagi flakon va shirin-ziravorli hid. Kechki partiyalarning yulduzi."),
    ("Giorgio Armani", "Acqua di Giò", "men", "edt", "aquatic", 1996, "Alberto Morillas",
     "#A9C9D8", "classic", "silver", 1_650_000,
     (["Laym", "Limon", "Bergamot", "Neroli"], ["Dengiz notalari", "Yasmin", "Shaftoli", "Rozmarin"],
      ["Oq mushk", "Kedr", "Eman moxi", "Pachuli"]),
     "warm", "day", 3, 3, set(),
     "O'rta yer dengizi shabadasi. Yozgi kunlar uchun toza va tetiklantiruvchi klassika."),
    ("Versace", "Eros", "men", "edt", "fougere", 2012, "Aurélien Guichard",
     "#4FA3A5", "facet", "gold", 1_350_000,
     (["Yalpiz", "Yashil olma", "Limon"], ["Tonka loviya", "Ambroksan", "Geran"],
      ["Vanil", "Vetiver", "Eman moxi", "Kedr"]),
     "cold", "evening", 4, 5, {"bestseller"},
     "Yunon sevgi xudosi sharafiga. Yalpiz, yashil olma va vanil — kuchli va jozibali."),
    ("Yves Saint Laurent", "Y", "men", "edp", "fougere", 2018, "Dominique Ropion",
     "#2E3A4B", "tall", "silver", 1_950_000,
     (["Olma", "Zanjabil", "Bergamot"], ["Shalfey", "Archa mevasi", "Geran"],
      ["Anbar yog'ochi", "Tonka loviya", "Kedr", "Vetiver"]),
     "all", "any", 4, 4, {"new"},
     "Orzulari sari intilayotgan avlod uchun. Toza oq ko'ylak va qora kurtkadek — oddiy va mukammal."),
    ("Tom Ford", "Ombré Leather", "men", "edp", "leather", 2018, "Sonia Constant",
     "#5A3E2B", "classic", "black", 3_300_000,
     (["Hil"], ["Teri", "Yasmin"], ["Anbar", "Eman moxi", "Pachuli"]),
     "cold", "evening", 5, 4, set(),
     "Amerika cho'llari va yumshoq qora teri. Kuchli, ammo nafis — xarakterli erkak uchun."),
    ("Dolce & Gabbana", "Light Blue Pour Homme", "men", "edt", "citrus", 2007, "Alberto Morillas",
     "#8EC5E8", "classic", "silver", 1_300_000,
     (["Greypfrut", "Bergamot", "Mandarin", "Archa mevasi"], ["Qalampir", "Rozmarin", "Atirgul daraxti"],
      ["Mushk", "Ladan", "Eman moxi"]),
     "warm", "day", 3, 3, set(),
     "Sitsiliya qirg'og'idagi yozgi kun. Muzdek sitrus va dengiz havosi."),
    ("Carolina Herrera", "Bad Boy", "men", "edt", "oriental", 2019, "Quentin Bisch, Nicolas Beaulieu",
     "#2D2D2D", "tall", "black", 1_650_000,
     (["Oq qalampir", "Qora qalampir", "Bergamot"], ["Shalfey", "Kedr"],
      ["Tonka loviya", "Kakao", "Anbar yog'ochi"]),
     "cold", "evening", 4, 4, set(),
     "Chaqmoq shaklidagi flakon va kakaoli qora tomon. Jasur, zamonaviy, esda qolarli."),
    ("Creed", "Aventus", "men", "edp", "chypre", 2010, "Olivier Creed, Erwin Creed",
     "#39424A", "classic", "silver", 5_200_000,
     (["Ananas", "Bergamot", "Qora smorodina", "Olma"], ["Qayin", "Pachuli", "Yasmin", "Atirgul"],
      ["Mushk", "Eman moxi", "Ambra", "Vanil"]),
     "all", "any", 4, 4, {"bestseller"},
     "G'alaba va kuch ramzi. Dudlangan qayin va ananas — nish parfyumeriyaning eng mashhur erkak atiri."),
    ("Amouage", "Interlude Man", "men", "edp", "oriental", 2012, "Pierre Negrin",
     "#4B6170", "facet", "gold", 4_200_000,
     (["Oregano", "Qalampir", "Bergamot"], ["Ladan", "Anbar", "Opoponaks"],
      ["Teri", "Ud", "Sandal", "Pachuli"]),
     "cold", "evening", 5, 5, set(),
     "Tartibsizlik ichidagi tinchlik. Ladan tutuni va ud — bu atir xonaga siz bilan birga kiradi."),
    ("Lattafa", "Asad", "men", "edp", "oriental", 2021, "",
     "#3A2E2A", "square", "gold", 390_000,
     (["Qora qalampir", "Ananas", "Tamaki"], ["Qahva", "Pachuli", "Iris"],
      ["Vanil", "Anbar", "Benzoin", "Labdanum"]),
     "cold", "evening", 5, 4, {"new"},
     "Sher yuragi — ziravorli qalampir, qahva va vanil. Narxidan ancha qimmat taassurot qoldiradi."),

    # — Uniseks / nish —
    ("Maison Francis Kurkdjian", "Baccarat Rouge 540", "unisex", "edp", "oriental", 2015, "Francis Kurkdjian",
     "#C8553D", "facet", "gold", 4_900_000,
     (["Za'faron", "Yasmin"], ["Anbar yog'ochi", "Ambra"], ["Archa smolasi", "Kedr"]),
     "all", "evening", 5, 5, {"bestseller"},
     "Baccarat billuri sharafiga yaratilgan she'r. Za'faron va anbar yog'ochining havodor, "
     "porloq izi — uni hech kim bilan adashtirib bo'lmaydi."),
    ("Tom Ford", "Tobacco Vanille", "unisex", "edp", "gourmand", 2007, "Olivier Gillotin",
     "#8B5A2B", "classic", "gold", 3_600_000,
     (["Tamaki", "Ziravorlar"], ["Vanil", "Kakao", "Tonka loviya"], ["Quritilgan mevalar", "Yog'och notalari"]),
     "cold", "evening", 5, 4, set(),
     "Londonning eski janoblar klubi: tamaki bargi, vanil va quritilgan mevalar. Qishning eng iliq hidi."),
    ("Tom Ford", "Lost Cherry", "unisex", "edp", "gourmand", 2018, "Louise Turner",
     "#8E1B2C", "classic", "black", 4_100_000,
     (["Qora gilos", "Gilos likyori", "Achchiq bodom"], ["Atirgul", "Yasmin"],
      ["Tonka loviya", "Peru balzami", "Sandal", "Vanil"]),
     "cold", "evening", 4, 4, {"new"},
     "Taqiqlangan meva: pishgan qora gilos va likyor. Shirin, mast qiluvchi va jozibali."),
    ("Byredo", "Gypsy Water", "unisex", "edp", "woody", 2008, "Jérôme Epinette",
     "#D8CFB6", "classic", "black", 3_250_000,
     (["Bergamot", "Limon", "Qalampir", "Archa mevasi"], ["Ladan", "Qarag'ay ignalari", "Iris"],
      ["Anbar", "Vanil", "Sandal"]),
     "warm", "day", 3, 3, set(),
     "Erkin sayohatchilar romantikasi: qarag'ay o'rmoni, gulxan va iliq qum."),
    ("Le Labo", "Santal 33", "unisex", "edp", "woody", 2011, "Frank Voelkl",
     "#CBB797", "classic", "silver", 3_900_000,
     (["Hil", "Binafsha", "Iris"], ["Ambroksan", "Papirus"], ["Sandal", "Kedr", "Teri"]),
     "all", "any", 4, 4, set(),
     "Nyu-Yorkning eng taniqli hidi. Quruq sandal va teri — kreativ insonlar imzosi."),
    ("Initio", "Oud for Greatness", "unisex", "edp", "woody", 2018, "",
     "#3D2E24", "square", "black", 4_300_000,
     (["Za'faron", "Muskat yong'og'i", "Lavanda"], ["Ud"], ["Pachuli", "Mushk"]),
     "cold", "evening", 5, 5, set(),
     "Buyuklik uchun ud. Za'faron va lavanda bilan yumshatilgan zamonaviy, toza ud."),
    ("Montale", "Intense Cafe", "unisex", "edp", "gourmand", 2013, "Pierre Montale",
     "#6F4E37", "classic", "silver", 1_650_000,
     (["Atirgul"], ["Qahva", "Vanil"], ["Anbar", "Oq mushk"]),
     "cold", "any", 5, 4, set(),
     "Ertalabki qahva va atirgul. Iliq, qulay va tanaga yopishib turadigan gurmand."),
    ("Creed", "Silver Mountain Water", "unisex", "edp", "citrus", 1995, "Olivier Creed",
     "#B9C7D4", "classic", "silver", 4_600_000,
     (["Bergamot", "Mandarin"], ["Yashil choy", "Qora smorodina"], ["Mushk", "Petitgren", "Sandal", "Galbanum"]),
     "warm", "day", 3, 3, set(),
     "Shveytsariya Alp tog'laridagi muzdek buloq. Yashil choy va sitrusning toza nafasi."),
    ("Kilian Paris", "Angels' Share", "unisex", "edp", "gourmand", 2020, "Benoist Lapouza",
     "#B5651D", "square", "gold", 4_500_000,
     (["Konyak"], ["Doljin", "Tonka loviya", "Eman"], ["Pralin", "Vanil", "Sandal"]),
     "cold", "evening", 4, 4, {"new", "bestseller"},
     "«Farishtalar ulushi» — eman bochkada pishgan konyak, doljin va pralin. Kuzning eng chiroyli hidi."),
    ("Jo Malone London", "Wood Sage & Sea Salt", "unisex", "edc", "aquatic", 2014, "Christine Nagel",
     "#C9D6CE", "classic", "silver", 1_750_000,
     (["Ambrett urug'i"], ["Dengiz tuzi"], ["Shalfey"]),
     "warm", "day", 2, 2, set(),
     "Shamolli qirg'oq, dengiz tuzi va yovvoyi shalfey. Minimalist va juda toza."),
    ("Lattafa", "Khamrah", "unisex", "edp", "gourmand", 2022, "",
     "#9C4A1E", "facet", "gold", 450_000,
     (["Doljin", "Muskat yong'og'i", "Bergamot"], ["Xurmo", "Pralin", "Tuberoza"],
      ["Vanil", "Tonka loviya", "Anbar yog'ochi", "Mirra", "Benzoin"]),
     "cold", "evening", 5, 5, {"new", "bestseller"},
     "Xurmo, doljin va pralin — sharqona shirinlik. Angels' Share muxlislariga hamyonbop muqobil."),
    ("Maison Francis Kurkdjian", "Gentle Fluidity Silver", "unisex", "edp", "woody", 2019, "Francis Kurkdjian",
     "#C7CCD1", "facet", "silver", 3_700_000,
     (["Archa mevasi", "Muskat yong'og'i", "Kashnich"], ["Mushk", "Ambroksan"], ["Anbar yog'ochi", "Vanil"]),
     "all", "any", 4, 3, set(),
     "Bir formulaning ikki talqinidan biri: archa mevasi va mushkning metalldek toza, salqin ovozi."),
]

REVIEW_NAMES = ["Madina", "Dilnoza", "Sardor", "Jasur", "Malika", "Shahzoda", "Bekzod", "Nilufar",
                "Aziza", "Javlon", "Kamola", "Otabek", "Zarina", "Sherzod", "Gulnoza", "Ulug'bek",
                "Sevara", "Akmal", "Lola", "Islom"]
REVIEW_TEXTS = {
    5: ["Ajoyib hid! Kun bo'yi saqlanadi, hamkasblarim doim nima sepganimni so'rashadi.",
        "Original ekanligiga shubha yo'q, qadoqlash ham juda chiroyli edi. Rahmat!",
        "Uchinchi marta olyapman. Yetkazib berish tez — ertasi kuni keldi.",
        "Sovg'aga oldim, juda xursand bo'lishdi. Sovg'a qadog'i alohida rahmat!",
        "Probnikdan sinab ko'rib, keyin katta flakon oldim. Afsuslanmadim.",
        "Eng sevimli atirim. Shleyfi zo'r, ortingdan iz qoladi."],
    4: ["Hid juda yoqdi, faqat issiqda tezroq tarqalib ketadi.",
        "Yaxshi atir, lekin men kutgandan biroz shirinroq ekan.",
        "Sifat a'lo, narxi biroz qimmat, lekin original uchun arziydi.",
        "Kechqurunga zo'r, kundalik uchun biroz og'irroq."],
    3: ["Yomon emas, lekin menga emas ekan. Probnikdan boshlashni maslahat beraman."],
}


def round_price(value, step=10_000):
    return int(round(value / step) * step)


class Command(BaseCommand):
    help = "AtirMagaz uchun demo katalog va ma'lumotlarni yaratadi"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Katalogni o'chirib, qayta yaratish")

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        quiet = options["verbosity"] == 0
        if reset:
            Review.objects.all().delete()
            Variant.objects.all().delete()
            Perfume.objects.all().delete()
            Brand.objects.all().delete()
            Note.objects.all().delete()
        elif Perfume.objects.exists():
            self.stdout.write(self.style.WARNING(
                "Katalog allaqachon to'ldirilgan. Qayta yaratish uchun: seed_atir --reset"))
            return

        rnd = random.Random(540)
        brands = {}
        for name, country, founded, niche, desc in BRANDS:
            brands[name] = Brand.objects.create(
                name=name, slug=slugify(name), country=country, founded=founded,
                is_niche=niche, description=desc)

        notes = {}

        def note(name):
            if name not in notes:
                notes[name] = Note.objects.create(name=name, slug=slugify(name) or f"nota-{len(notes)}")
            return notes[name]

        for i, row in enumerate(PERFUMES):
            (brand, name, gender, conc, family, year, perfumer, color, shape, cap, price100,
             (top, heart, base), season, tod, longevity, sillage, flags, desc) = row
            perfume = Perfume.objects.create(
                brand=brands[brand], name=name, slug=slugify(f"{brand} {name}"),
                gender=gender, concentration=conc, family=family, year=year, perfumer=perfumer,
                description=desc, season=season, time_of_day=tod,
                longevity=longevity, sillage=sillage, color=color, shape=shape, cap=cap,
                is_new="new" in flags, is_bestseller="bestseller" in flags,
                sold_count=rnd.randint(40, 400) + (600 if "bestseller" in flags else 0),
            )
            perfume.top_notes.set([note(n) for n in top])
            perfume.heart_notes.set([note(n) for n in heart])
            perfume.base_notes.set([note(n) for n in base])

            # Har uchinchi atirga chegirma
            on_sale = i % 3 == 1
            sizes = [(50, 0.68), (100, 1.0)] if price100 < 1_000_000 else [(30, 0.52), (50, 0.72), (100, 1.0)]
            for volume, k in sizes:
                price = round_price(price100 * k)
                old = None
                if on_sale:
                    old = price
                    price = round_price(price * 0.85)
                Variant.objects.create(
                    perfume=perfume, volume_ml=volume, price=price, old_price=old,
                    stock=0 if (i % 11 == 4 and volume == 30) else rnd.randint(3, 25))
            if price100 >= 1_000_000:
                Variant.objects.create(
                    perfume=perfume, volume_ml=5, is_sample=True,
                    price=round_price(price100 * 0.075, 5_000), stock=rnd.randint(10, 40))

            for _ in range(rnd.randint(2, 6)):
                rating = rnd.choices([5, 4, 3], weights=[70, 25, 5])[0]
                Review.objects.create(
                    perfume=perfume, name=rnd.choice(REVIEW_NAMES), rating=rating,
                    text=rnd.choice(REVIEW_TEXTS[rating]))

        PromoCode.objects.get_or_create(code="ATIR10", defaults={
            "percent": 10, "description": "Birinchi buyurtma uchun"})
        PromoCode.objects.get_or_create(code="KUZ20", defaults={
            "percent": 20, "min_total": 1_500_000, "description": "Kuzgi aksiya, 1.5 mln so'mdan"})

        User = get_user_model()
        # Serverda admin ensure_admin buyrug'i bilan, muhitdagi parol orqali yaratiladi
        if settings.DEBUG and not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@atirmagaz.uz", "admin12345")
            if not quiet:
                self.stdout.write("Admin yaratildi: admin / admin12345")

        if not quiet:
            self.stdout.write(self.style.SUCCESS(
                f"Tayyor: {Brand.objects.count()} brend, {Perfume.objects.count()} atir, "
                f"{Note.objects.count()} nota, {Review.objects.count()} sharh."))
