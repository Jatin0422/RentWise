const profileToggle = document.querySelector(".profile-toggle");
const profileSidebar = document.querySelector("#profile-sidebar");
const profileClose = document.querySelector(".profile-close");
const profileBackdrop = document.querySelector(".profile-backdrop");

function openProfile() {
    if (!profileSidebar || !profileBackdrop || !profileToggle) return;
    profileSidebar.classList.add("is-open");
    profileSidebar.setAttribute("aria-hidden", "false");
    profileToggle.setAttribute("aria-expanded", "true");
    profileBackdrop.hidden = false;
}

function closeProfile() {
    if (!profileSidebar || !profileBackdrop || !profileToggle) return;
    profileSidebar.classList.remove("is-open");
    profileSidebar.setAttribute("aria-hidden", "true");
    profileToggle.setAttribute("aria-expanded", "false");
    profileBackdrop.hidden = true;
}

profileToggle?.addEventListener("click", openProfile);
profileClose?.addEventListener("click", closeProfile);
profileBackdrop?.addEventListener("click", closeProfile);

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeProfile();
    }
});
