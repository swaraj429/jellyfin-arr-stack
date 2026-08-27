const servicesEl = document.getElementById("services");
const statusText = document.getElementById("statusText");
const serviceCount = document.getElementById("serviceCount");
const lastUpdated = document.getElementById("lastUpdated");
const refreshButton = document.getElementById("refreshButton");

const icons = {
    sonarr: "◉",
    radarr: "◆",
    prowlarr: "⌕",
    qbit: "⇩",
    seerr: "✦"
};

async function loadServices() {

    try {

        const response =
            await fetch("/api/services", {
                cache: "no-store"
            });

        if (!response.ok) {
            throw new Error("Dashboard API unavailable");
        }

        const data = await response.json();

        renderServices(data.services);

        statusText.textContent = "All systems ready";

        serviceCount.textContent =
            `${data.services.length} services discovered`;

        lastUpdated.textContent =
            `Updated ${new Date().toLocaleTimeString()}`;

    } catch (error) {

        console.error(error);

        statusText.textContent = "Dashboard error";

        serviceCount.textContent =
            "Unable to discover services";

        servicesEl.innerHTML = `
            <div class="empty">
                Unable to load services.
                <br><br>
                Check the dashboard container.
            </div>
        `;
    }
}


function renderServices(services) {

    if (!services.length) {

        servicesEl.innerHTML = `
            <div class="empty">
                No reverse proxy services discovered.
            </div>
        `;

        return;
    }

    servicesEl.innerHTML =
        services.map(service => {

            const key =
                service.name
                    .toLowerCase()
                    .replace(/\s+/g, "");

            const icon =
                icons[key] || "◆";

            return `
                <a
                    class="service"
                    href="${service.path}"
                >

                    <div>

                        <div class="service-top">

                            <div class="service-icon">
                                ${icon}
                            </div>

                            <div class="service-arrow">
                                ↗
                            </div>

                        </div>

                        <h3>
                            ${escapeHtml(service.name)}
                        </h3>

                        <div class="service-path">
                            ${escapeHtml(service.path)}
                        </div>

                    </div>

                    <div class="service-bottom">

                        <span class="service-status"></span>

                        Available

                    </div>

                </a>
            `;

        }).join("");
}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


refreshButton.addEventListener(
    "click",
    loadServices
);


loadServices();

setInterval(
    loadServices,
    30000
);
