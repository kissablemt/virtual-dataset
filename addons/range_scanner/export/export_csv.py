import csv
import numpy as np
import os

def export(filePath, fileName, mappedData, exportNoiseData, data):
    print("Exporting data into .csv format...")

    with open(os.path.join(filePath, "%s.csv" % fileName), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        if exportNoiseData:
            # write header to file
            # writer.writerow("categoryID;partID;X;Y;Z;distance;X_noise;Y_noise;Z_noise;distance_noise;intensity;red;green;blue;")
            writer.writerow([
                "cls_index",
                "object_id",
                "X",
                "Y",
                "Z",
                "distance",
                "X_noise",
                "Y_noise",
                "Z_noise",
                "distance_noise",
                "intensity",
                "red",
                "green",
                "blue",
            ])

            for i, hit in enumerate(mappedData):
                # concatenate each entry and write it to a file
                # fast string joining: https://stackoverflow.com/a/2721561/13440564
                # number to string conversion: https://stackoverflow.com/a/15263885/13440564
                # a precision of .3 should be enough as we don't need sub-millimeter accuracy 

                # write data to file
                # writer.writerow("%d;%d;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f" %
                #     (   
                #         hit[0], hit[1],
                #         hit[2], hit[3], hit[4], 
                #         hit[5],
                #         hit[10], hit[11], hit[12], 
                #         hit[13], 
                #         hit[6],
                #         hit[7], hit[8], hit[9]
                #     )
                # )
                writer.writerow([
                    "%d" % data[i].target.get("cls_index", 0),
                    "%d" % data[i].target.get("object_id", 0),
                    "%.6f" % hit[2],
                    "%.6f" % hit[3],
                    "%.6f" % hit[4],
                    "%.6f" % hit[5],
                    "%.6f" % hit[10],
                    "%.6f" % hit[11],
                    "%.6f" % hit[12],
                    "%.6f" % hit[13],
                    "%.6f" % hit[6],
                    "%.6f" % hit[7],
                    "%.6f" % hit[8],
                    "%.6f" % hit[9],
                ])
        else:
            # write header to file
            # writer.writerow("categoryID;partID;X;Y;Z;distance;intensity;red;green;blue;")
            writer.writerow([
                "cls_index",
                "object_id",
                "X",
                "Y",
                "Z",
                "distance",
                "intensity",
                "red",
                "green",
                "blue",
            ])

            for i, hit in enumerate(mappedData):
                # writer.writerow("%d;%d;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f;%.3f" %
                #     (
                #         hit[0], hit[1],
                #         hit[2], hit[3], hit[4], 
                #         hit[5],
                #         hit[6],
                #         hit[7], hit[8], hit[9]
                #     )
                # )
                writer.writerow([
                    "%d" % data[i].target.get("cls_index", 0),
                    "%d" % data[i].target.get("object_id", 0),
                    "%.6f" % hit[2],
                    "%.6f" % hit[3],
                    "%.6f" % hit[4],
                    "%.6f" % hit[5],
                    "%.6f" % hit[6],
                    "%.6f" % hit[7],
                    "%.6f" % hit[8],
                    "%.6f" % hit[9],
                ])
    print("Done.")