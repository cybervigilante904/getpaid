async function sendLocation(position) {

    const latitude =
        position.coords.latitude;

    const longitude =
        position.coords.longitude;

    const accuracy =
        position.coords.accuracy;


    await fetch(
        `/api/location/${SESSION_ID}`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                latitude,
                longitude,
                accuracy
            })
        }
    );
}


const watchId =
    navigator.geolocation.watchPosition(
        sendLocation,
        handleLocationError,
        {
            enableHighAccuracy: true,
            maximumAge: 2000,
            timeout: 10000
        }
    );