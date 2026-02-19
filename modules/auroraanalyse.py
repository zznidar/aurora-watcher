import numpy as np

# Constants: ratios and thresholds
GRmin = 1.05
GBmin = 1.05

Gmin = 60

BIG = 0.1
SMALL = 0.005

STRONG = 1.30
MEDIUM = 1.15


@pyscript_compile
def analyse(img_array):
    # Get image dimensions and crop to top 5/8 of the image
    visina, sirina = img_array.shape[:2]
    img_cropped = img_array[:visina * 5 // 8, :, :]

    # Extract RGB channels
    r = img_cropped[:, :, 0].astype(float)
    g = img_cropped[:, :, 1].astype(float)
    b = img_cropped[:, :, 2].astype(float)
    
    # Avoid division by zero
    r_safe = np.where(r == 0, 1, r)
    b_safe = np.where(b == 0, 1, b)
    
    # Calculate ratios
    g_r_ratio = g / r_safe
    g_b_ratio = g / b_safe
    
    # Create mask for aurora pixels
    aurora_mask = (g_r_ratio > GRmin) & (g_b_ratio > GBmin) & (g > Gmin)
    
    # Count aurora pixels and calculate intensities
    auroraPixels = np.sum(aurora_mask).item()
    auroraIntensities = np.sum((g_r_ratio + g_b_ratio) / 2 * aurora_mask).item()
    totalPixels = img_cropped.shape[0] * img_cropped.shape[1]

    ratioAuroraPixels = auroraPixels/totalPixels
    ratioAuroraIntensities = (auroraIntensities/auroraPixels) if ratioAuroraPixels > 0 else 0
    ratioAuroraIntensitiesTotal = auroraIntensities/totalPixels

    print("Aurora pixels", auroraPixels, "Total pixels", totalPixels, "Ratio aurora/total", ratioAuroraPixels, "Ratio aurora intensities", ratioAuroraIntensities, "Ratio aurora intensities total", ratioAuroraIntensitiesTotal)

    out = calculateStrength(ratioAuroraPixels, ratioAuroraIntensities)
    out["auroraPixels3"] = auroraPixels
    return(out)

@pyscript_compile
def calculateStrength(ratioAuroraPixels, ratioAuroraIntensities):

    out = {
        "sizeType3": "none",
        "strengthType3": "none",
        "size3": 0,
        "strength3": 0
    }

    if(ratioAuroraPixels < SMALL):
        out["sizeType3"] = "none"
        print("No aurora")
        return(out)
    elif(ratioAuroraPixels < 2*SMALL):
        out["sizeType3"] = "small"
    else:
        out["sizeType3"] = "big"

    out["size3"] = round((ratioAuroraPixels/(BIG)*100), 2) # in percent


    if(ratioAuroraIntensities < MEDIUM):
        out["strengthType3"] = "weak"
    else:
        out["strengthType3"] = "strong"
    
    out["strength3"] = round((ratioAuroraIntensities/(STRONG)*100), 2) # in percent

    print(out)
    return(out)
