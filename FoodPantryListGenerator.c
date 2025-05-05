// FoodPantryListGenerator.cpp : This file contains the 'main' function. Program execution begins and ends there.
//



//Modified C Program with a do - while Loop:
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_BARCODE_LENGTH 100

int main() {
    int i = 0;
    int adjctr = 0;
    char barcode[MAX_BARCODE_LENGTH];
    char adjustedbc[MAX_BARCODE_LENGTH];
    FILE* file;
    char continueScanning;
    char* bracketptr = NULL;
    int recordCount = 0;
    char line[256];  // Buffer to read lines
    char rootPath[256]; // Adjust size as needed
    //time_t rawtime = time(NULL);;
    //struct tm* timeinfo = NULL;
    time_t t = time(NULL);
    struct tm tm = *localtime(&t);

    // Open the CSV file (in append mode to add new data)
    // Build the file path
    sprintf(rootPath, "scanned_barcodes20%02d%02d%02d.csv", tm.tm_year % 100, tm.tm_mon + 1, tm.tm_mday);
    
    printf("Root Path: %s\n", rootPath);
    
	// Open the file in append mode
    file = fopen(rootPath, "a+");
    if (file == NULL) {
        printf("Error opening file!\n");
        return 1;
    }

    // Review the file for number of records
    // Move to the beginning to count existing records
    rewind(file);
    while (fgets(line, sizeof(line), file) != NULL) {
        recordCount++;
    }

    printf("Current number of records: %d\n", recordCount);

    // Ready to add more records
    
    do {
        memset(barcode, 0, sizeof(barcode));
        // Ask the user to scan a barcode
        printf("Record %d Please scan a barcode: ",++recordCount);

        // Capture the barcode from the user (it simulates the scanner input)
        fgets(barcode, sizeof(barcode), stdin);

        // Remove the newline character from the input if it exists
        size_t length = strlen(barcode);
        if (length < 2) break;
        if (barcode[length - 1] == '\n') {
            barcode[length - 1] = '\0';
        }
        // change barcode from {[C]01052089} to C1052089
        adjctr = 0;
        i = 4;
        memset(adjustedbc, 0, sizeof(adjustedbc));
        adjustedbc[adjctr++] = 'C';
        while (barcode[i] == '0')
        {
            i++;

        }
        strcat(&adjustedbc[adjctr], &barcode[i]);
        if ((bracketptr = strchr(adjustedbc, '}')) != NULL)
        {
            *bracketptr = 0;
        }

        // Write the scanned barcode to the CSV file with a comma separator
        //fprintf(file, "%s,\n", barcode);

        // wrtie the adjusted barcode to the CSV file with a comma separator
        //fprintf(file, "%s,\n", adjustedbc);
        // Ask the user if they want to scan another barcode
       // printf("Do you want to scan another barcode? (y/n): ");
        //scanf(" %c", &continueScanning);
       // getchar();  // To consume the newline character left by scanf

        // add date-time

        time_t rawtime;
        struct tm* timeinfo;

        // Get the current time
        time(&rawtime);
        timeinfo = localtime(&rawtime);
        // Declare a buffer to store the formatted time string
        char time_str[20];

        // Store the formatted date and time in the time_str variable
        snprintf(time_str, sizeof(time_str), "%d/%d/%d% d:%d",
            timeinfo->tm_mon + 1, timeinfo->tm_mday,
            timeinfo->tm_year + 1900, timeinfo->tm_hour, timeinfo->tm_min);

        // Print the date and time in the desired format
        fprintf(file, "%s,,,,,%s\n", adjustedbc,time_str);
        //printf("%02d/%02d/%04d%02d:%02d\n", timeinfo->tm_mon + 1, timeinfo->tm_mday,
          //  timeinfo->tm_year + 1900, timeinfo->tm_hour, timeinfo->tm_min);
        if (length < 2)
        {
            break;
        }
        else {
            continueScanning = 'y';
        }
    } while (continueScanning == 'y' || continueScanning == 'Y');

    // Close the file after writing all barcodes
    fclose(file);

    printf("Barcodes saved to:%s\n",rootPath);

    return 0;
}


//#include <stdio.h>
//#include <stdlib.h>
//#include <string.h>
//
//#define MAX_BARCODE_LENGTH 100
//
//int main() {
//    char barcode[MAX_BARCODE_LENGTH];
//    FILE* file;
//
//    // Open the CSV file (in append mode to add new data)
//    file = fopen("scanned_barcodes.csv", "a");
//    if (file == NULL) {
//        printf("Error opening file!\n");
//        return 1;
//    }
//
//    printf("Please scan a barcode: ");
//
//    // Capture the barcode from the user (it simulates the scanner input)
//    fgets(barcode, sizeof(barcode), stdin);
//
//    // Remove the newline character from the input if it exists
//    size_t length = strlen(barcode);
//    if (barcode[length - 1] == '\n') {
//        barcode[length - 1] = '\0';
//    }
//
//    // Write the scanned barcode to the CSV file with a comma separator (assuming a single field)
//    fprintf(file, "%s,\n", barcode);
//
//    // Close the file after writing
//    fclose(file);
//
//    printf("Barcode saved to 'scanned_barcodes.csv'\n");
//
//    return 0;
//}
//
 

// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
// Debug program: F5 or Debug > Start Debugging menu

// Tips for Getting Started: 
//   1. Use the Solution Explorer window to add/manage files
//   2. Use the Team Explorer window to connect to source control
//   3. Use the Output window to see build output and other messages
//   4. Use the Error List window to view errors
//   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
//   6. In the future, to open this project again, go to File > Open > Project and select the .sln file
