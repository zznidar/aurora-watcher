var slikaWidth, slikaHeight; // original size

var sirina, visina; // resized size
var imgdata, arr_shallow, arr; // "global" vars

// If debug, we don't have debug
var debug = (new URL(window.location.href)).searchParams.get("debug") !== null;
console.log("Debug: ", debug);

function initialise(slika) {
    console.warn("Started");
    console.log(slika.width, slika.height);
    sirina = slikaWidth = slika.width
    visina = slikaHeight = slika.height

    // Resize image if greater than 2000x2000 px
    resize = true;
    if((sirina > 2000 || visina > 2000) && resize) {
        console.log("resizing", sirina, visina, "divide by 2");
        sirina = sirina>>>1;
        visina = visina>>>1;
    }

    canvas.width = sirina
    canvas.height = visina


    context.drawImage(base_image, 0, 0, sirina, visina);

    // Only read from canvas once as it is very CPU/GPU-demanding
    imgdata = context.getImageData(0, 0, sirina, visina); // TODO: Split canvas evenly among threads
    arr_shallow = imgdata.data;
    arr = Uint8ClampedArray.from(arr_shallow) // This shall not be modified to allow multiple-pass processing.

    return({"visina": visina, "sirina": sirina, "resized": sirina != slikaWidth})
}

/* GRmin = 1.3;
GRmax = 1.5;
GBmin = 1.2;
GBmax = 1.3; */

/* GRmin = 1.12;
GBmin = 1.12; */
GRmin = 1.05;
GBmin = 1.05;

Gmin = 60;

// ratioAuroraPixels: 0.1 = strong; 0.01 = weak // acutally aurora size
// ratioAuroraIntensities: 1.30 = strong; 1.15 = medium

BIG = 0.1;
//SMALL = 0.01;
SMALL = 0.005;

STRONG = 1.30;
MEDIUM = 1.15;

function analyse() {
    totalPixels = 0;
    auroraPixels = 0;
    auroraIntensities = 0;
    for(let i = 0; i < sirina; i++) {
        for(let j = 0; j < Math.floor(visina * 5/8); j++) { // Bottom three eights of image are dark window border, no aurora there
            let [r, g, b, a] = getArrPixelColour(i, j);
            //console.log("Barva", r, g, b, a);
            //if(GRmin < g/r && g/r < GRmax && GBmin < g/b && g/b < GBmax) {
            if(GRmin < g/r && GBmin < g/b && g > Gmin) {
                setPixels(i, j, 255, 0, 0, 255);
                auroraPixels++;
                auroraIntensities += (g/(r||1) + g/(b||1))/2;
            }
            totalPixels++;
        }
    }

    context.putImageData(imgdata, 0, 0);
    ratioAuroraPixels = auroraPixels/totalPixels;
    ratioAuroraIntensities = (auroraIntensities/auroraPixels) || 0;
    ratioAuroraIntensitiesTotal = auroraIntensities/totalPixels;
    console.log("Aurora pixels", auroraPixels, "Total pixels", totalPixels, "Ratio aurora/total", ratioAuroraPixels, "Ratio aurora intensities", ratioAuroraIntensities, "Ratio aurora intensities total", ratioAuroraIntensitiesTotal);

    let strength = calculateStrength(ratioAuroraPixels, ratioAuroraIntensities);
    document.getElementById("outputText").innerHTML = `Aurora size: ${strength[0]}, Aurora strength: ${strength[1]}`;
}

function calculateStrength(ratioAuroraPixels, ratioAuroraIntensities) {
    let size, strength;
    if(ratioAuroraPixels < SMALL) {
        size = "none";
        console.log("No aurora");
        return(["none", "none"]);
    } else if(ratioAuroraPixels < 2*SMALL) {
        size = "small";
    } else {
        size = `${(ratioAuroraPixels/(BIG)*100).toFixed(2)} % big`;
    }

    if(ratioAuroraIntensities < MEDIUM) {
        strength = "weak";
    } else {
        strength = `${(ratioAuroraIntensities/(STRONG)*100).toFixed(2)} % strong`;
    }

    console.log(size, strength);
    return([size, strength]);

}


function setPixels(x, y, r, g, b, a) {
    //return;
    arr_shallow[0 + 4*x + 4*sirina*y] = r;
    arr_shallow[1 + 4*x + 4*sirina*y] = g;
    arr_shallow[2 + 4*x + 4*sirina*y] = b;
    arr_shallow[3 + 4*x + 4*sirina*y] = a;

}

function getArrPixelColour(x, y) {
    return([arr[0 + 4*x + 4*sirina*y], arr[1 + 4*x + 4*sirina*y], arr[2 + 4*x + 4*sirina*y], arr[3 + 4*x + 4*sirina*y]]);
}


function getAverageColour(x, y, width, height) {
    let sum = [0, 0, 0, 0];
    let count = 0;
    for(let i = x; i < x + width; i++) {
        for(let j = y; j < y + height; j++) {
            let [r, g, b, a] = arr.slice(0 + 4*i + 4*sirina*j, 4 + 4*i + 4*sirina*j);
            sum[0] += r;
            sum[1] += g;
            sum[2] += b;
            sum[3] += a;
            count++;
        }
    }
    return(sum.map(x => Math.round(x/count)))
}

