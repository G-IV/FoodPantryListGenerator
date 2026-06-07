# List Generator Volunteer Position
## Scan-In Verification Station

*Last updated: 05/23/2026*

---

## Overview

The process of entering data is most accurate when there is a second step, called **verification**, that is performed to check the accuracy of the first entry of data.

The volunteer will use a scanner to read the barcode ID card/image of everyone entering the Sunrise Room to shop. If the person is a proxy for someone else (they will be carrying a "proxy" card), please scan the barcode ID card/image of the **household for which they are picking up**.

The program used is named **FoodPantryListGenerator**. It is not an Oasis program, so the volunteer does not have to be a trained Oasis volunteer who has passed the Confidentiality Quiz.

The volunteer will have a basket in which to collect the letter cards that identify which group each customer is in. These cards come in white and an assortment of colors. In addition, there will be some yellow-orange cards that first-time and re-certified customers will carry that say "Newly Registered and Ready to Shop." Collect those also.

---

## Getting Ready (First Shift Volunteer)

The first shift volunteer for this station will find the Surface Pro computer and a Tera scanner both plugged and charging. There is a plastic box with a lid sitting on the floor underneath the table.

1. Unplug both devices from power and store the charging cables into the two labeled plastic bags in the plastic box. One is labeled **Surface Pro Charger** and the other is labeled **Tera Scanner Charger**.
2. Open the Surface Pro computer and turn it on using the **left button at the top of the screen**. (There are two buttons — the other controls the volume, which you shouldn't need.)
3. Press the **Enter** key on the keyboard to log in to the computer.
4. Remove the small plastic **dongle** stored in the bottom of the scanner and plug it into the **USB port on the right side of the display screen**.
5. Turn the scanner on by pressing the trigger. It will play musical notes to indicate it is ready to scan.

---

## Scanning Barcodes

The Surface Pro with the List Generator software is labeled with a sticker with the letter **"L"** on the cover. (There is a spare Surface Pro labeled **"M"** that also has the List Generator software installed.)

There is a desktop icon titled **"FoodPantry ListGenerator"**. To open the program at the beginning of pantry, **double-click the icon**.

The screen will display a startup message showing the filename (the date in the filename will be today's date) and the number of records already in the file.

<!-- TODO: Add screenshot of startup screen here -->
<!-- ![Startup screen](images/startup-screen.png) -->

Use the scanner to read each customer's barcode ID card or image. The screen will display the case number from the barcode and then prompt you to scan the next one.

<!-- TODO: Add screenshot of scanning prompt here -->
<!-- ![Scanning prompt](images/scanning-prompt.png) -->

> **Duplicate scans:** If you accidentally scan a barcode twice in a row, the program will display a green **"Duplicate scan — proceed to next customer"** message. No action is needed — the duplicate is not saved to the list.

> **Already served today:** If a barcode that was scanned **earlier in the current session** is scanned again (and it was not the immediately prior scan), the program will silently skip the duplicate scan. No alert is shown and no action is needed.

### If a Barcode Won't Scan

Occasionally a customer's barcode will not scan, or they will present a yellow **"Forgot Card"** slip of paper. When that happens:

1. Key in the customer's case number **without the letter C** and press **Enter**.
2. If the customer presented a "Forgot Card" slip, keep it until the end of pantry, then **throw it out** so the customer cannot use it again.

### Exiting and Re-entering the Program

- To **exit** the program, press **Enter** on a blank scan prompt.
- To **re-enter** the program, double-click the **FoodPantry ListGenerator** icon.
- If the program is **already open** and you double-click the icon again, a message will appear and the new window will close on its own after you press Enter. Click the existing program window in the taskbar at the bottom of the screen.

### During a Lull

If you have downtime, sort the cards from the basket by color/letter and group them together. There should be eight to ten of each letter and several "Newly Registered" cards. The color/letter cards will go back to Station 1 and the "Newly Registered" cards will go back to Stations 1 and 2.

---

## After 11:30am

This station, along with Station 1 in the foyer, will not close down until **12:10pm**. Station 1 will have reduced paperwork after 11:30am to expedite late arrivals. This will **not** affect your standard processing at this station.

---

## Closing Down (Second Shift Volunteer)

1. Take note of how many customers have been entered into the file — everyone will want to know that number.
2. Press **Enter** on the keyboard to close the program.
3. Remove the dongle from the USB port on the right of the computer and put it back into the bottom of the Tera scanner.
4. Place the picture frame from the table **face-down at the bottom of the plastic box** to protect it.

### Transferring the File to the Thumb Drive

1. Remove the dongle from the USB port.
2. Put the dongle into the bottom of the Tera scanner.
3. Insert the **thumb drive** (found in the plastic box) into the USB port.
4. Open **File Explorer** and navigate to: `This PC > Windows (C:) > DoubleCheck`
5. Locate the file named `scanned_barcodes` followed by today's date (e.g., `scanned_barcodes20260104.csv`).
6. Copy it to the **D: drive** (the thumb drive).
7. Give the thumb drive to **Tina**, or leave it in the plastic box if you cannot find her.

---

## About the Scanner

The scanner used at this station is the **Tera D5100 2D Wireless Barcode Scanner**. If you need the user manual (for example, to troubleshoot pairing the dongle or adjust scanner settings), it is available on the product page:

https://tera-digital.com/products/2d-barcode-scanner-d5100

---

## Oasis Administrator Role

This section is for the **Oasis Administrator** — the person responsible for maintaining the flagged-barcode list (`InvNmbrs.csv`) and for responding when the List Generator station contacts them about a blocked scan.

Volunteers do not need to read this section. Administrators do not need to read the sections above.

---

### Your Role on Pantry Day

<!-- TODO (Tina): Add a brief description of the Oasis Admin's broader pantry-day responsibilities here — e.g. staffing the Oasis stations, reviewing records, handling flagged cases, etc. This section should give a new admin enough context to understand where the InvNmbrs.csv task fits into the overall pantry workflow. -->

The task specific to the List Generator is: **maintaining `InvNmbrs.csv`**, a file on the Surface Pro that controls which case numbers are blocked from being logged at the scan-in station. See the sections below for how to manage it.

---

### What the Volunteer Sees When a Barcode Is Flagged

When a volunteer scans a barcode that appears in `InvNmbrs.csv`, the screen immediately displays a red banner like this:

```
  This barcode has been flagged, please ask a cart guide to escort customer to Oasis administrator
```

The volunteer will then pause and contact you using the information shown in the banner. **Scanning continues normally after the flagged scan** — no action is required from the volunteer beyond contacting you. The flagged case number is **not** written to the scanned output file, but it **is** recorded in a separate flagged barcode log for your review (see [Reviewing the Flagged Barcode Log](#reviewing-the-flagged-barcode-log) below).

Once you have resolved the situation, see [Removing a Flagged Case Number](#removing-a-flagged-case-number) below if the customer should be cleared to receive assistance.

---

### What Is InvNmbrs.csv?

`InvNmbrs.csv` is a plain text file stored on the Surface Pro at:

```
C:\DoubleCheck\InvNmbrs.csv
```

**The List Generator does not create this file automatically.** You must create it manually before the first pantry day. See [Setting Up the File for the First Time](#setting-up-the-file-for-the-first-time) below.

If the file is absent the program runs normally — all barcodes are treated as valid and no flagging occurs.

The List Generator reads this file every time a barcode is scanned, so any changes you make take effect immediately — you do not need to restart the program.

---

### Setting Up the File for the First Time

Before the first pantry day, you must create `InvNmbrs.csv` manually:

1. Open **File Explorer** and navigate to `This PC > Windows (C:) > DoubleCheck`.
2. Right-click in the folder, choose **New > Text Document**.
3. Name the file `InvNmbrs.csv` — be sure to include `.csv` and remove the default `.txt` extension.
   - If you do not see file extensions in File Explorer, go to **View > Show > File name extensions** and check the box.
4. Right-click the file and choose **Open with > Notepad**.
5. Type the column header on the first line:

```
Case #
```

6. Save the file (`Ctrl+S`).

The file is now ready. See [Adding a Flagged Case Number](#adding-a-flagged-case-number) to add case numbers to it.

> **If the file was accidentally deleted**, follow the steps above again to recreate it. The List Generator will continue to run normally without it — no barcodes will be flagged until it is restored.

---

### Creating the File Manually

To create `InvNmbrs.csv` from scratch:

1. Open **File Explorer** and navigate to `This PC > Windows (C:) > DoubleCheck`.
2. Right-click in the folder, choose **New > Text Document**.
3. Name the file `InvNmbrs.csv` — be sure to include `.csv` and remove the default `.txt` extension.
   - If you do not see file extensions in File Explorer, go to **View > Show > File name extensions** and check the box.
4. Right-click the file and choose **Open with > Notepad**.
5. Type the column header on the first line:

```
Case #
```

6. Save the file (`Ctrl+S`).

---

### Adding a Flagged Case Number

1. Open `C:\DoubleCheck\InvNmbrs.csv` in Notepad.
2. Add one case number per line after the `Case #` header row.  
   Use the `C`-prefix format (e.g. `C1052089`) — this is the same format shown on the screen when the volunteer scans a card.
3. Save the file (`Ctrl+S`).

The change takes effect on the very next scan at the List Generator station — no restart needed.

**Example file with two flagged case numbers:**

```
Case #
C1052089
C1052090
```

---

### Reviewing the Flagged Barcode Log

Every time a flagged barcode is scanned, the List Generator records the case number and the time of the scan in a separate log file:

```
C:\DoubleCheck\flagged_barcodes20YYMMDD.csv
```

The date in the filename matches the date of the session (e.g. `flagged_barcodes20260505.csv` for May 5, 2026).

**To review it after pantry:**

1. Open **File Explorer** and navigate to `This PC > Windows (C:) > DoubleCheck`.
2. Open `flagged_barcodes20YYMMDD.csv` (today's date) in Notepad or Excel.
3. Each row shows a case number and the time it was scanned:

```
C1052089,5/5/2026 9:15
C1052090,5/5/2026 9:47
```

This file is created only when at least one flagged barcode is scanned. If no flagged barcodes were encountered during the session, the file will not exist.

If a flagged barcode was scanned multiple times in one session, each scan appears as a separate row in chronological order.

---

### Reviewing the Already-Served Log

> **Note:** Already-served logging is currently disabled. Non-consecutive re-scans are silently skipped and are not written to a log file. This section will be updated when the feature is re-enabled.

---

### Removing a Flagged Case Number

1. Open `C:\DoubleCheck\InvNmbrs.csv` in Notepad.
2. Delete the line containing the case number you want to clear.
3. Save the file (`Ctrl+S`).

The next time the volunteer scans that barcode, it will be logged normally.

---

### File Format Reference

| Row | Content | Example |
|-----|---------|----------|
| 1 | Column header — type this exactly | `Case #` |
| 2 and below | One flagged case number per line | `C1052089` |

- Case numbers must include the `C` prefix.
- One case number per line — do not put multiple numbers on the same line.
- Blank lines between case numbers are fine and will be ignored.
- The file is re-read on every scan, so edits take effect immediately.
