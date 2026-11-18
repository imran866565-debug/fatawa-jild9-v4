#!/usr/bin/env python3
"""Merge Fatawa Razviya Jild 9 easy-Urdu tashreeh v4 chunks into jild-09.json.

Reads the 18 chunk files listed in chunks-manifest-v4-jild09.json,
concatenates them in order 01 -> 18, derives start_page = min(pages)
where the field is absent, normalises page markers, validates, and
writes {"masail": [...]} to jild-09.json.

ORDER -- chunk order is the order (no quirk, unlike Jild 1 Part 2):
  The v3 merged file ~/workspace/fatawa-app/content/tashreeh/jild-09.json
  has ID order == concatenation order of the v4 chunks 01..18 (verified
  locally by the coordinator: all 325 ids match the v3 sequence exactly).
  Do NOT sort or reorder. Within each chunk, items keep file order.

NO RENAME QUIRK in Jild 9: the v3 merged file has 325 UNIQUE ids — the
  book numbers no masala twice in this jild (unlike Jild 5, which had
  two masail 263 and two masail 304, and Jild 6, which had two masail
  774). Chunk ids are used exactly as written; the merge asserts
  duplicate-free ids instead of renaming anything.
  NOTE: masala-138 spans the chunk 07/08 boundary; v3 already
  disambiguates the two parts as jild9-masala-138-alif (chunk 07 end)
  and plain jild9-masala-138 (chunk 08 start). Those are v3 ids, kept
  exactly — they are NOT merge renames. Likewise chunk 11's first id
  jild9-masala-198-tail and chunk 06's first id jild9-masala-85-87 are
  v3 ids, kept exactly.

START_PAGE: every one of the 18 v4 chunks carries start_page ==
  min(pages) for all its items (verified by the coordinator). The
  derivation code below stays as a safety net; it is expected to
  derive 0 items.

MARKER NORMALISATION (the only text transformation): page markers, if
  present, are normalised to the single form [safha N] written with the
  Urdu word for page:
  - lenticular-bracket form (U+3010/U+3011 around the Urdu word for
    page + number) -> [safha N]
  - [short form] -> [safha N]
  - [safha N] stays as-is
  Applied to every string field of every item (jawab, sawal, title,
  notes). The 18 v4 chunks contain ZERO markers of any form (verified
  locally), so normalisation is expected to be a no-op here; the code
  stays so the merge is robust and the "none remain" assertions still
  run. No other text is touched and no markers are invented.
  NOTE: the literal lenticular-bracket characters are written here only
  as U+3010/U+3011 escapes, never as literal characters in this file.

VALIDATION (fails loudly on any violation):
  325 items; ID sequence EXACTLY == the v3 merged file's ID sequence
  (embedded below as V3_IDS, copied verbatim from
  ~/workspace/fatawa-app/content/tashreeh/jild-09.json); pages per item
  identical to v3 (embedded as V3_PAGES, same source, verified against
  the v3 file before pushing); 863 unique pages (min 6, max 950);
  volume_ids == {49}; start_page == min(pages) for every item (after
  derivation); zero empty tashreeh_jawab; no lenticular / short markers
  remain; first id jild9-p6, last id jild9-p949.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = "chunks-manifest-v4-jild09.json"

# Concatenation order: chunk files 01 -> 18, in order.
CHUNK_ORDER = [f"jild-09-chunk-{n:02d}.json" for n in range(1, 19)]

EXPECTED_ITEMS = 325
EXPECTED_PAGES = 863
EXPECTED_MIN_PAGE = 6
EXPECTED_MAX_PAGE = 950
EXPECTED_VOLUME_IDS = {49}
EXPECTED_FIRST_ID = "jild9-p6"
EXPECTED_LAST_ID = "jild9-p949"

# v3 ID sequence, verbatim from content/tashreeh/jild-09.json.
V3_IDS = ['jild9-p6', 'jild9-p9', 'jild9-masala-1', 'jild9-masala-2', 'jild9-masala-3', 'jild9-masala-4', 'jild9-masala-5', 'jild9-masala-6', 'jild9-masala-7', 'jild9-masala-8', 'jild9-masala-9', 'jild9-masala-10', 'jild9-masala-11', 'jild9-masala-12', 'jild9-masala-13', 'jild9-masala-14', 'jild9-masala-15', 'jild9-p109', 'jild9-p113', 'jild9-p120', 'jild9-p133', 'jild9-masala-16', 'jild9-masala-17', 'jild9-masala-18', 'jild9-masala-19', 'jild9-masala-20', 'jild9-masala-21', 'jild9-masala-22', 'jild9-masala-23', 'jild9-masala-24', 'jild9-p159', 'jild9-masala-25', 'jild9-masala-26', 'jild9-masala-27', 'jild9-masala-28', 'jild9-masala-29', 'jild9-masala-30', 'jild9-masala-31', 'jild9-masala-32', 'jild9-masala-33', 'jild9-masala-34', 'jild9-masala-35', 'jild9-masala-36', 'jild9-masala-37', 'jild9-masala-38', 'jild9-masala-39', 'jild9-masala-40', 'jild9-masala-41', 'jild9-masala-42', 'jild9-masala-43', 'jild9-masala-44', 'jild9-masala-45', 'jild9-masala-46', 'jild9-masala-47', 'jild9-masala-49', 'jild9-masala-50', 'jild9-masala-51', 'jild9-masala-52', 'jild9-masala-53', 'jild9-masala-54', 'jild9-masala-55', 'jild9-masala-56', 'jild9-masala-57', 'jild9-masala-58', 'jild9-masala-59', 'jild9-masala-60', 'jild9-masala-61', 'jild9-masala-62', 'jild9-masala-63', 'jild9-masala-64', 'jild9-masala-65', 'jild9-masala-66', 'jild9-masala-67-70', 'jild9-masala-71', 'jild9-masala-72-78', 'jild9-masala-79-80', 'jild9-masala-81', 'jild9-masala-82', 'jild9-masala-83', 'jild9-masala-84', 'jild9-masala-85-87', 'jild9-p319', 'jild9-p324', 'jild9-p328', 'jild9-p342', 'jild9-p345', 'jild9-p348', 'jild9-p354', 'jild9-p361', 'jild9-p368', 'jild9-p369', 'jild9-masala-88', 'jild9-masala-89', 'jild9-masala-90', 'jild9-masala-91', 'jild9-masala-92-93', 'jild9-masala-94', 'jild9-masala-95', 'jild9-masala-96', 'jild9-masala-97', 'jild9-masala-98', 'jild9-masala-99-102', 'jild9-masala-103', 'jild9-masala-104', 'jild9-masala-105-109', 'jild9-masala-106', 'jild9-masala-107', 'jild9-masala-108', 'jild9-masala-109', 'jild9-masala-110', 'jild9-masala-111', 'jild9-masala-112', 'jild9-masala-113', 'jild9-masala-114', 'jild9-masala-115', 'jild9-masala-116', 'jild9-masala-117', 'jild9-masala-118', 'jild9-masala-119-120', 'jild9-masala-121', 'jild9-masala-122', 'jild9-masala-123', 'jild9-masala-124', 'jild9-masala-125', 'jild9-masala-126', 'jild9-masala-127', 'jild9-masala-128-129', 'jild9-masala-130', 'jild9-masala-131', 'jild9-masala-132', 'jild9-masala-133-134', 'jild9-masala-135', 'jild9-masala-136', 'jild9-masala-137', 'jild9-masala-138-alif', 'jild9-masala-138', 'jild9-p441', 'jild9-p457', 'jild9-p477', 'jild9-masala-139', 'jild9-masala-140', 'jild9-masala-146', 'jild9-masala-147', 'jild9-masala-148', 'jild9-masala-149', 'jild9-masala-150', 'jild9-masala-151', 'jild9-masala-153', 'jild9-masala-154', 'jild9-masala-156', 'jild9-masala-158', 'jild9-masala-159', 'jild9-p529', 'jild9-masala-163', 'jild9-masala-164', 'jild9-masala-165', 'jild9-masala-167', 'jild9-masala-168', 'jild9-masala-169', 'jild9-masala-177', 'jild9-masala-178', 'jild9-masala-179', 'jild9-masala-180', 'jild9-masala-181', 'jild9-p543', 'jild9-masala-182', 'jild9-masala-183', 'jild9-masala-184', 'jild9-masala-185', 'jild9-masala-186', 'jild9-masala-187', 'jild9-masala-188', 'jild9-masala-196', 'jild9-masala-198-tail', 'jild9-masala-199', 'jild9-masala-200', 'jild9-masala-201-204', 'jild9-masala-205', 'jild9-masala-206', 'jild9-masala-207-209', 'jild9-masala-210', 'jild9-masala-211', 'jild9-masala-212', 'jild9-masala-213', 'jild9-masala-214', 'jild9-masala-215-216', 'jild9-masala-217-218', 'jild9-masala-219-222', 'jild9-masala-223', 'jild9-masala-224', 'jild9-masala-225', 'jild9-masala-226-228', 'jild9-masala-229', 'jild9-masala-230', 'jild9-masala-231', 'jild9-masala-232', 'jild9-masala-233', 'jild9-masala-234', 'jild9-masala-235', 'jild9-masala-236-239', 'jild9-masala-240', 'jild9-masala-241', 'jild9-masala-242', 'jild9-masala-243-244', 'jild9-masala-245', 'jild9-masala-246', 'jild9-masala-247', 'jild9-masala-248-250', 'jild9-masala-251-255', 'jild9-masala-256', 'jild9-masala-257', 'jild9-masala-258', 'jild9-masala-259', 'jild9-masala-260', 'jild9-masala-261', 'jild9-masala-262', 'jild9-masala-263-268', 'jild9-masala-264', 'jild9-masala-265', 'jild9-masala-266', 'jild9-masala-267', 'jild9-masala-269', 'jild9-masala-270', 'jild9-masala-271', 'jild9-p677', 'jild9-masala-272', 'jild9-p682', 'jild9-p683', 'jild9-p684', 'jild9-p685', 'jild9-p687', 'jild9-p688', 'jild9-p690', 'jild9-p691', 'jild9-p693', 'jild9-p696', 'jild9-p700', 'jild9-p702', 'jild9-p703', 'jild9-p706', 'jild9-p708', 'jild9-p710', 'jild9-p712', 'jild9-p715', 'jild9-p716', 'jild9-p718', 'jild9-p720', 'jild9-p722', 'jild9-p725', 'jild9-p726', 'jild9-p728', 'jild9-p730', 'jild9-p733', 'jild9-p735', 'jild9-p737', 'jild9-p739', 'jild9-p741', 'jild9-p743', 'jild9-p745', 'jild9-p746', 'jild9-p747', 'jild9-p750', 'jild9-p753', 'jild9-p754', 'jild9-p757', 'jild9-p760', 'jild9-p763', 'jild9-p767', 'jild9-p769', 'jild9-p772', 'jild9-p776', 'jild9-p779', 'jild9-p780', 'jild9-p782', 'jild9-p786', 'jild9-p789', 'jild9-p795', 'jild9-p801', 'jild9-p805', 'jild9-p810', 'jild9-p812', 'jild9-p823', 'jild9-p828', 'jild9-p832', 'jild9-p834', 'jild9-p836', 'jild9-p838', 'jild9-p841', 'jild9-p844', 'jild9-p846', 'jild9-p848', 'jild9-p851', 'jild9-p854', 'jild9-p858', 'jild9-p862', 'jild9-p866', 'jild9-p870', 'jild9-p874', 'jild9-p877', 'jild9-p881', 'jild9-p882', 'jild9-p884', 'jild9-p886', 'jild9-p888', 'jild9-p890', 'jild9-p895', 'jild9-p897', 'jild9-p898', 'jild9-p902', 'jild9-p903', 'jild9-p904', 'jild9-p907', 'jild9-p910', 'jild9-p911', 'jild9-p914', 'jild9-p916', 'jild9-p919', 'jild9-p921', 'jild9-p930', 'jild9-p934', 'jild9-p937', 'jild9-p941', 'jild9-p943', 'jild9-p947', 'jild9-p949']

# v3 pages per item id, verbatim from content/tashreeh/jild-09.json.
V3_PAGES = {
"jild9-p6": [6, 7, 8],
"jild9-p9": [9],
"jild9-masala-1": [82, 83],
"jild9-masala-2": [83, 84, 85, 86, 87, 88, 89, 90, 91],
"jild9-masala-3": [91],
"jild9-masala-4": [92],
"jild9-masala-5": [92, 93],
"jild9-masala-6": [93, 94, 95],
"jild9-masala-7": [95, 96],
"jild9-masala-8": [96, 97],
"jild9-masala-9": [97, 98, 99],
"jild9-masala-10": [99],
"jild9-masala-11": [99, 100],
"jild9-masala-12": [100],
"jild9-masala-13": [100, 101, 102, 103, 104, 105],
"jild9-masala-14": [106, 107],
"jild9-masala-15": [108, 109],
"jild9-p109": [109, 110, 111, 112, 113],
"jild9-p113": [113, 114, 115, 116, 117, 118, 119, 120],
"jild9-p120": [120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133],
"jild9-p133": [133, 134, 135],
"jild9-masala-16": [136],
"jild9-masala-17": [136, 137],
"jild9-masala-18": [137, 138],
"jild9-masala-19": [139],
"jild9-masala-20": [139],
"jild9-masala-21": [139],
"jild9-masala-22": [139, 140],
"jild9-masala-23": [140, 141, 142, 143, 144, 145, 146, 147, 148, 149],
"jild9-masala-24": [149, 150, 151, 152, 153, 154, 155, 156, 157, 158],
"jild9-p159": [159],
"jild9-masala-25": [159],
"jild9-masala-26": [159],
"jild9-masala-27": [159, 160, 161, 162],
"jild9-masala-28": [162, 163],
"jild9-masala-29": [163, 164],
"jild9-masala-30": [164],
"jild9-masala-31": [164, 165],
"jild9-masala-32": [165, 166, 167, 168],
"jild9-masala-33": [168, 169],
"jild9-masala-34": [169, 170],
"jild9-masala-35": [170, 171, 172],
"jild9-masala-36": [172, 173],
"jild9-masala-37": [173, 174],
"jild9-masala-38": [175],
"jild9-masala-39": [175, 176, 177],
"jild9-masala-40": [177, 178, 179, 180, 181, 182, 183],
"jild9-masala-41": [183, 184],
"jild9-masala-42": [184, 185],
"jild9-masala-43": [185],
"jild9-masala-44": [185, 186, 187],
"jild9-masala-45": [187],
"jild9-masala-46": [187, 188, 189],
"jild9-masala-47": [189, 190],
"jild9-masala-49": [190, 191],
"jild9-masala-50": [191],
"jild9-masala-51": [191, 192],
"jild9-masala-52": [192, 193],
"jild9-masala-53": [193],
"jild9-masala-54": [193, 194],
"jild9-masala-55": [194, 195],
"jild9-masala-56": [194, 195],
"jild9-masala-57": [195],
"jild9-masala-58": [195],
"jild9-masala-59": [195, 196],
"jild9-masala-60": [196],
"jild9-masala-61": [197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208],
"jild9-masala-62": [210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224],
"jild9-masala-63": [225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239],
"jild9-masala-64": [240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257],
"jild9-masala-65": [258, 259],
"jild9-masala-66": [259, 260, 261, 262, 263],
"jild9-masala-67-70": [263, 264, 265],
"jild9-masala-71": [265],
"jild9-masala-72-78": [265, 266, 267],
"jild9-masala-79-80": [267],
"jild9-masala-81": [267, 268],
"jild9-masala-82": [268],
"jild9-masala-83": [270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315],
"jild9-masala-84": [315, 316],
"jild9-masala-85-87": [318, 319],
"jild9-p319": [319, 320, 321, 322, 323, 324],
"jild9-p324": [324, 325, 326, 327, 328],
"jild9-p328": [328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342],
"jild9-p342": [342, 343, 344, 345],
"jild9-p345": [345, 346, 347, 348],
"jild9-p348": [348, 349, 350, 351, 352, 353, 354],
"jild9-p354": [354, 355, 356, 357, 358, 359, 360, 361],
"jild9-p361": [361, 362, 363, 364, 365, 366, 367, 368],
"jild9-p368": [368],
"jild9-p369": [369, 370],
"jild9-masala-88": [370],
"jild9-masala-89": [370, 371],
"jild9-masala-90": [372],
"jild9-masala-91": [372, 373],
"jild9-masala-92-93": [373],
"jild9-masala-94": [373, 374],
"jild9-masala-95": [374],
"jild9-masala-96": [374],
"jild9-masala-97": [374, 375, 376, 377, 378],
"jild9-masala-98": [378, 379, 380],
"jild9-masala-99-102": [380, 381],
"jild9-masala-103": [381, 382],
"jild9-masala-104": [382, 383],
"jild9-masala-105-109": [383, 384, 385, 386],
"jild9-masala-106": [386],
"jild9-masala-107": [386, 387, 388, 389, 390, 391],
"jild9-masala-108": [391, 392],
"jild9-masala-109": [392, 393],
"jild9-masala-110": [393, 394, 395, 396, 397, 398, 399, 400, 401],
"jild9-masala-111": [401, 402],
"jild9-masala-112": [402],
"jild9-masala-113": [402, 403, 404],
"jild9-masala-114": [404],
"jild9-masala-115": [404, 405],
"jild9-masala-116": [405, 406],
"jild9-masala-117": [406, 407],
"jild9-masala-118": [407],
"jild9-masala-119-120": [407, 408],
"jild9-masala-121": [408],
"jild9-masala-122": [408, 409],
"jild9-masala-123": [409, 410],
"jild9-masala-124": [410, 411, 412, 413],
"jild9-masala-125": [413],
"jild9-masala-126": [413],
"jild9-masala-127": [413, 414, 415, 416, 417, 418, 419, 420],
"jild9-masala-128-129": [420, 421],
"jild9-masala-130": [421],
"jild9-masala-131": [421, 422, 423, 424, 425],
"jild9-masala-132": [425, 426],
"jild9-masala-133-134": [426],
"jild9-masala-135": [427],
"jild9-masala-136": [427, 428],
"jild9-masala-137": [428],
"jild9-masala-138-alif": [428, 429],
"jild9-masala-138": [430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441],
"jild9-p441": [441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457],
"jild9-p457": [457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477],
"jild9-p477": [477, 478, 479],
"jild9-masala-139": [480],
"jild9-masala-140": [480, 481],
"jild9-masala-146": [481, 482],
"jild9-masala-147": [482, 483],
"jild9-masala-148": [483, 484],
"jild9-masala-149": [486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523],
"jild9-masala-150": [523, 524],
"jild9-masala-151": [524],
"jild9-masala-153": [524],
"jild9-masala-154": [524, 525],
"jild9-masala-156": [525, 526],
"jild9-masala-158": [527],
"jild9-masala-159": [527, 528],
"jild9-p529": [529],
"jild9-masala-163": [529, 530, 531, 532, 533],
"jild9-masala-164": [533],
"jild9-masala-165": [533, 534],
"jild9-masala-167": [534],
"jild9-masala-168": [535, 536],
"jild9-masala-169": [536, 537, 538],
"jild9-masala-177": [538],
"jild9-masala-178": [538, 539],
"jild9-masala-179": [539],
"jild9-masala-180": [539, 540],
"jild9-masala-181": [542, 543],
"jild9-p543": [543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565],
"jild9-masala-182": [565, 566, 567, 568],
"jild9-masala-183": [570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593],
"jild9-masala-184": [594],
"jild9-masala-185": [594, 595],
"jild9-masala-186": [595, 596],
"jild9-masala-187": [596, 597],
"jild9-masala-188": [597, 598],
"jild9-masala-196": [598, 599, 600],
"jild9-masala-198-tail": [601],
"jild9-masala-199": [601],
"jild9-masala-200": [601, 602],
"jild9-masala-201-204": [602, 603],
"jild9-masala-205": [603],
"jild9-masala-206": [603, 604],
"jild9-masala-207-209": [604, 605],
"jild9-masala-210": [605, 606],
"jild9-masala-211": [606, 607],
"jild9-masala-212": [607],
"jild9-masala-213": [607, 608, 609],
"jild9-masala-214": [609, 610],
"jild9-masala-215-216": [610],
"jild9-masala-217-218": [610],
"jild9-masala-219-222": [612, 613],
"jild9-masala-223": [613, 614],
"jild9-masala-224": [614, 615],
"jild9-masala-225": [615],
"jild9-masala-226-228": [615, 616],
"jild9-masala-229": [616],
"jild9-masala-230": [617],
"jild9-masala-231": [617],
"jild9-masala-232": [617, 618],
"jild9-masala-233": [618],
"jild9-masala-234": [618],
"jild9-masala-235": [618, 619, 620, 621, 622],
"jild9-masala-236-239": [622, 623, 624, 625],
"jild9-masala-240": [625, 626, 627, 628, 629, 630, 631],
"jild9-masala-241": [631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644],
"jild9-masala-242": [644, 645],
"jild9-masala-243-244": [645],
"jild9-masala-245": [645, 646],
"jild9-masala-246": [646],
"jild9-masala-247": [646, 647],
"jild9-masala-248-250": [647, 648],
"jild9-masala-251-255": [648],
"jild9-masala-256": [648, 649],
"jild9-masala-257": [649],
"jild9-masala-258": [650],
"jild9-masala-259": [650],
"jild9-masala-260": [651, 652, 653, 654, 655, 656, 657, 658],
"jild9-masala-261": [659],
"jild9-masala-262": [659],
"jild9-masala-263-268": [659, 660, 661],
"jild9-masala-264": [661],
"jild9-masala-265": [661],
"jild9-masala-266": [663, 664, 665, 666, 667, 668, 669],
"jild9-masala-267": [669],
"jild9-masala-269": [670, 671, 672, 673, 674],
"jild9-masala-270": [674, 675],
"jild9-masala-271": [675],
"jild9-p677": [677, 678],
"jild9-masala-272": [679, 680, 681],
"jild9-p682": [682, 683],
"jild9-p683": [683, 684],
"jild9-p684": [684, 685],
"jild9-p685": [685, 686, 687],
"jild9-p687": [687, 688],
"jild9-p688": [688, 689, 690],
"jild9-p690": [690, 691],
"jild9-p691": [691, 692, 693],
"jild9-p693": [693, 694, 695],
"jild9-p696": [696, 697, 698, 699, 700],
"jild9-p700": [700, 701],
"jild9-p702": [702, 703],
"jild9-p703": [703, 704, 705, 706],
"jild9-p706": [706, 707, 708],
"jild9-p708": [708, 709, 710],
"jild9-p710": [710, 711, 712],
"jild9-p712": [712, 713, 714, 715],
"jild9-p715": [715, 716],
"jild9-p716": [716, 717, 718],
"jild9-p718": [718, 719, 720],
"jild9-p720": [720, 721, 722],
"jild9-p722": [722, 723, 724, 725],
"jild9-p725": [725, 726],
"jild9-p726": [726, 727, 728],
"jild9-p728": [728, 729, 730],
"jild9-p730": [730, 731, 732],
"jild9-p733": [733, 734, 735],
"jild9-p735": [735, 736, 737],
"jild9-p737": [737, 738, 739],
"jild9-p739": [739, 740],
"jild9-p741": [741, 742],
"jild9-p743": [743, 744],
"jild9-p745": [745, 746],
"jild9-p746": [746, 747],
"jild9-p747": [747, 748, 749, 750],
"jild9-p750": [750, 751, 752, 753],
"jild9-p753": [753, 754],
"jild9-p754": [754, 755, 756, 757],
"jild9-p757": [757, 758, 759, 760],
"jild9-p760": [760, 761, 762, 763],
"jild9-p763": [763, 764, 765, 766, 767],
"jild9-p767": [767, 768, 769],
"jild9-p769": [769, 770, 771, 772],
"jild9-p772": [772, 773, 774, 775, 776],
"jild9-p776": [776, 777, 778, 779],
"jild9-p779": [779, 780],
"jild9-p780": [780, 781, 782],
"jild9-p782": [782, 783, 784, 785],
"jild9-p786": [786, 787, 788, 789],
"jild9-p789": [789, 790, 791, 792, 793, 795],
"jild9-p795": [795, 796, 797, 798, 799, 800, 801],
"jild9-p801": [801, 802, 803, 804, 805],
"jild9-p805": [805, 806, 807, 808, 809, 810],
"jild9-p810": [810, 811, 812],
"jild9-p812": [812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823],
"jild9-p823": [823, 824, 825, 826, 827],
"jild9-p828": [828, 829, 830, 831],
"jild9-p832": [832, 833],
"jild9-p834": [834, 835],
"jild9-p836": [836, 837],
"jild9-p838": [838, 839, 840],
"jild9-p841": [841, 842, 843],
"jild9-p844": [844, 845],
"jild9-p846": [846, 847],
"jild9-p848": [848, 849, 850],
"jild9-p851": [851, 852, 853],
"jild9-p854": [854, 855, 856, 857],
"jild9-p858": [858, 859, 860, 861],
"jild9-p862": [862, 863, 864, 865],
"jild9-p866": [866, 867, 868, 869],
"jild9-p870": [870, 871, 872, 873],
"jild9-p874": [874, 875, 876],
"jild9-p877": [877, 878, 879, 880],
"jild9-p881": [881, 882],
"jild9-p882": [882, 883, 884],
"jild9-p884": [884, 885, 886],
"jild9-p886": [886, 887, 888],
"jild9-p888": [888, 889, 890],
"jild9-p890": [890, 891, 892, 893, 894],
"jild9-p895": [895, 896, 897],
"jild9-p897": [897, 898],
"jild9-p898": [898, 899, 900, 901],
"jild9-p902": [902, 903],
"jild9-p903": [903, 904],
"jild9-p904": [904, 905, 906],
"jild9-p907": [907, 908, 909, 910],
"jild9-p910": [910, 911],
"jild9-p911": [911, 912, 913, 914],
"jild9-p914": [914, 915],
"jild9-p916": [916, 917, 918],
"jild9-p919": [919, 920],
"jild9-p921": [921, 922, 923, 924, 925, 926, 927, 928, 929],
"jild9-p930": [930, 931, 932, 933],
"jild9-p934": [934, 935, 936],
"jild9-p937": [937, 938, 939, 940],
"jild9-p941": [941, 942],
"jild9-p943": [943, 944, 945, 946],
"jild9-p947": [947, 948],
"jild9-p949": [949, 950],
}

# The Urdu word for "page" is safha; the canonical marker is [safha N].
# Lenticular brackets are U+3010 (open) and U+3011 (close); the short
# form is "[safha-initial N]" with the single-letter abbreviation.
# All three patterns are built from escapes so this file never contains
# a literal lenticular-bracket pair.
SAFHA = "\u0635\u0641\u062d\u06c1"  # the Urdu word for page
RE_LENTICULAR = re.compile("\u3010" + SAFHA + " (\\d+)\u3011")
RE_SHORT = re.compile("\\[\u0635 (\\d+)\\]")
RE_FULL = re.compile("\\[" + SAFHA + " \\d+\\]")
LENTICULAR_PREFIX = "\u3010" + SAFHA  # for the "none remain" check
SHORT_PREFIX_RE = re.compile("\\[\u0635 \\d+\\]")

# Canonical output key order for every item (the JSON contract).
ITEM_KEYS = ["id", "title", "volume_id", "pages", "start_page",
             "tashreeh_sawal", "tashreeh_jawab", "notes"]


def normalise_markers(text):
    """Normalise page markers in one string. Returns (new_text, counts)."""
    counts = {"lenticular": 0, "short": 0, "full_before": 0}
    counts["full_before"] = len(RE_FULL.findall(text))
    text, n1 = RE_LENTICULAR.subn("[" + SAFHA + " \\1]", text)
    counts["lenticular"] = n1
    text, n2 = RE_SHORT.subn("[" + SAFHA + " \\1]", text)
    counts["short"] = n2
    return text, counts


def normalise_item(item):
    """Normalise markers in every string field of one item (recursively
    through lists/dicts). Returns per-form counts for this item."""
    totals = {"lenticular": 0, "short": 0, "full_before": 0}

    def walk(value):
        if isinstance(value, str):
            new, c = normalise_markers(value)
            for k in totals:
                totals[k] += c[k]
            return new
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value

    for key in list(item.keys()):
        item[key] = walk(item[key])
    return totals


def main():
    assert len(V3_IDS) == EXPECTED_ITEMS, "embedded V3_IDS length mismatch"
    assert set(V3_PAGES) == set(V3_IDS), "embedded V3_PAGES keys != V3_IDS"
    assert sum(len(v) for v in V3_PAGES.values()) >= EXPECTED_PAGES

    manifest = json.load(open(os.path.join(BASE, MANIFEST), encoding="utf-8"))
    entries = manifest["chunks"]
    assert len(entries) == 18, f"expected 18 manifest entries, got {len(entries)}"
    assert all(e.get("status") == "done" for e in entries), "not all chunks done"
    by_file = {e["file"]: e for e in entries}
    assert set(by_file) == set(CHUNK_ORDER), (
        f"manifest files != CHUNK_ORDER: "
        f"missing={set(CHUNK_ORDER) - set(by_file)} "
        f"extra={set(by_file) - set(CHUNK_ORDER)}"
    )

    all_items = []
    derived = []
    for fname in CHUNK_ORDER:
        path = os.path.join(BASE, fname)
        d = json.load(open(path, encoding="utf-8"))
        items = d["masail"]
        entry = by_file[fname]
        assert len(items) == entry["items"], (
            f"{fname}: {len(items)} items, manifest says {entry['items']}"
        )
        # Marker normalisation, with before/after counts per chunk.
        before = {"lenticular": 0, "short": 0, "full_before": 0}
        for it in items:
            c = normalise_item(it)
            for k in before:
                before[k] += c[k]
        after_full = sum(
            len(RE_FULL.findall(json.dumps(it, ensure_ascii=False)))
            for it in items
        )
        print(
            f"{fname}: {len(items)} items | markers before: "
            f"lenticular={before['lenticular']} short={before['short']} "
            f"full={before['full_before']} | after: full={after_full}"
        )
        assert after_full == (
            before["lenticular"] + before["short"] + before["full_before"]
        ), f"{fname}: marker count changed by normalisation!"
        # Derive start_page = min(pages) where absent (none expected: all chunks carry start_page).
        for it in items:
            if "start_page" not in it:
                it["start_page"] = min(it["pages"])
                derived.append(it["id"])
        all_items.extend(items)

    # NO RENAME QUIRK in Jild 9: the v3 merged file has 325 UNIQUE
    # ids — the book numbers no masala twice in this jild. Chunk ids
    # are used exactly as written.
    assert len(all_items) == len({it["id"] for it in all_items}), (
        f"DUPLICATE IDS before validation: "
        f"{[i for i in [it['id'] for it in all_items] if [it['id'] for it in all_items].count(i) > 1]}"
    )
    print("renames applied: [] (no duplicate masala numbers in Jild 9)")

    print(f"concatenated: {len(all_items)} items")
    print(f"start_page derived for {len(derived)} items (expected 0: all chunks carry start_page)")
    assert len(all_items) == EXPECTED_ITEMS, (
        f"expected {EXPECTED_ITEMS} items, got {len(all_items)}"
    )

    # Rebuild each item in the canonical key order (the JSON contract).
    canonical = []
    for it in all_items:
        assert set(it.keys()) == set(ITEM_KEYS), (
            f"{it.get('id')}: keys {sorted(it.keys())} != {sorted(ITEM_KEYS)}"
        )
        canonical.append({k: it[k] for k in ITEM_KEYS})
    all_items = canonical

    # Validation.
    ids = [it["id"] for it in all_items]
    assert ids == V3_IDS, (
        f"ID sequence != v3: first diff at "
        f"{next((i for i, (a, b) in enumerate(zip(ids, V3_IDS)) if a != b), min(len(ids), len(V3_IDS)))}"
    )
    assert len(ids) == len(set(ids)), (
        f"DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}"
    )
    empty = [it["id"] for it in all_items if not it.get("tashreeh_jawab")]
    assert not empty, f"EMPTY JAWAB: {empty}"
    vols = set(it.get("volume_id") for it in all_items)
    assert vols == EXPECTED_VOLUME_IDS, f"volume_ids {vols} != {EXPECTED_VOLUME_IDS}"
    pages = set()
    for it in all_items:
        assert it["pages"] == V3_PAGES[it["id"]], (
            f"{it['id']}: pages {it['pages']} != v3 {V3_PAGES[it['id']]}"
        )
        pages.update(it["pages"])
    assert len(pages) == EXPECTED_PAGES, (
        f"expected {EXPECTED_PAGES} unique pages, got {len(pages)}"
    )
    assert min(pages) == EXPECTED_MIN_PAGE, f"min page {min(pages)}"
    assert max(pages) == EXPECTED_MAX_PAGE, f"max page {max(pages)}"
    exceptions = {
        it["id"] for it in all_items if it["start_page"] != min(it["pages"])
    }
    assert not exceptions, f"start_page != min(pages): {sorted(exceptions)}"
    assert ids[0] == EXPECTED_FIRST_ID, f"first id {ids[0]}"
    assert ids[-1] == EXPECTED_LAST_ID, f"last id {ids[-1]}"

    out = {"masail": all_items}
    out_text = json.dumps(out, ensure_ascii=False, indent=1)
    assert LENTICULAR_PREFIX not in out_text, "lenticular markers remain in output!"
    assert not SHORT_PREFIX_RE.search(out_text), "short markers remain in output!"
    total_markers = len(RE_FULL.findall(out_text))
    print(
        f"VALIDATION PASSED: {len(all_items)} items, {len(pages)} unique pages "
        f"(min {min(pages)}, max {max(pages)}), volume_ids {sorted(vols)}, "
        f"first {ids[0]}, last {ids[-1]}, start_page == min(pages) for all, "
        f"derived start_page for {len(derived)} items, markers {total_markers}"
    )

    with open(os.path.join(BASE, "jild-09.json"), "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"WROTE jild-09.json: {len(out_text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
