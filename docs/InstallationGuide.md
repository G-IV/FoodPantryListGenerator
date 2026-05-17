# FoodPantryListGenerator — Installation Guide

## Who this is for

This guide is for anyone setting up FoodPantryListGenerator on a new computer, or updating it on an existing one. No developer experience is required.

---

## Contents

1. [Check for (or install) the trust certificate](#1-check-for-or-install-the-trust-certificate)
2. [Download the executable](#2-download-the-executable)
3. [Set up the working folder](#3-set-up-the-working-folder)
4. [Create the desktop shortcut](#4-create-the-desktop-shortcut)
5. [Verify the installation](#5-verify-the-installation)
6. [Updating to a new version](#updating-to-a-new-version)

---

## 1. Check for (or install) the trust certificate

The executable is signed with a self-signed certificate. Windows will block the application unless that certificate is installed as a trusted root on the computer. **This is a one-time step per computer.**

### Check whether the certificate is already installed

1. Press **Win + R**, type `certlm.msc`, and press **Enter**.
   *(If prompted by User Account Control, click **Yes**.)*
2. In the left panel, expand **Trusted Root Certification Authorities → Certificates**.
3. Look through the list for an entry whose **Issued To** column contains the name of the signing organization (for example, `St. Andrews` or similar).

**If you see it:** the certificate is already installed — skip to [step 2](#2-download-the-executable).

**If you do not see it:** follow the steps below to install it.

### Install the certificate

1. Download [`ChurchCert.cer`](ChurchCert.cer) from this repository.
   *(On GitHub: click the link, then click the **Download raw file** button — the arrow icon near the top right.)*
2. Locate the downloaded `ChurchCert.cer` and double-click it.
2. Click **Install Certificate**.
3. On the *Store Location* screen, select **Local Machine** and click **Next**.
   *(If prompted by User Account Control, click **Yes**.)*
4. Select **Place all certificates in the following store** and click **Browse**.
5. Select **Trusted Root Certification Authorities** and click **OK**.
6. Click **Next**, then **Finish**.
7. A dialog will say *"The import was successful."* Click **OK**.

The certificate is now installed. You can verify it by repeating the *Check* steps above — the entry should now appear in the list.

---

## 2. Download the executable

1. Open a browser and go to the [Releases page](https://github.com/G-IV/FoodPantryListGenerator/releases).
2. Click the latest release (the one marked **Latest**).
3. Under **Assets**, click **FoodPantryListGenerator.exe** to download it.

> **No SmartScreen warning expected:** because the certificate is installed, Windows should recognize the publisher and run the file without a warning. If you still see a SmartScreen prompt, confirm the certificate was installed correctly in step 1.

---

## 3. Set up the working folder

The application reads and writes its files in whatever folder the shortcut's *Start in* field points to. In production this is `C:\DoubleCheck\`.

1. Open **File Explorer**.
2. Navigate to `This PC → Windows (C:)`.
3. If a folder named `DoubleCheck` does not already exist, right-click → **New → Folder** and name it `DoubleCheck`.
4. Move or copy `FoodPantryListGenerator.exe` into `C:\DoubleCheck\`.

---

## 4. Create the desktop shortcut

If a shortcut does not already exist on the desktop:

1. In `C:\DoubleCheck\`, right-click `FoodPantryListGenerator.exe` → **Send to → Desktop (create shortcut)**.
2. Right-click the new shortcut on the desktop → **Properties**.
3. Confirm the fields match the following:

   | Field | Value |
   |-------|-------|
   | **Target** | `C:\DoubleCheck\FoodPantryListGenerator.exe` |
   | **Start in** | `C:\DoubleCheck\` |

4. In the **Shortcut** tab, change the name at the top (or rename the shortcut on the desktop) to `FoodPantry ListGenerator`.
5. Click **OK**.

> The **Start in** field is what causes the output CSV to be saved to `C:\DoubleCheck\` rather than a random default folder. Do not leave it blank.

---

## 5. Verify the installation

1. Double-click the **FoodPantry ListGenerator** shortcut on the desktop.
2. The program should open a console window displaying a startup message with today's date in the filename and a record count of 0 (or the count of records already in the file if one exists).
3. Type any number and press **Enter** — it should be accepted and displayed.
4. Press **Enter** on a blank line to exit.

If the program opens and responds correctly, the installation is complete.

---

## Updating to a new version

Updating does not require reinstalling the certificate or recreating the shortcut.

1. Go to the [Releases page](https://github.com/G-IV/FoodPantryListGenerator/releases) and download the latest `FoodPantryListGenerator.exe`.
2. Copy it to `C:\DoubleCheck\`, replacing the existing file.

The desktop shortcut and all existing data files are unaffected.
