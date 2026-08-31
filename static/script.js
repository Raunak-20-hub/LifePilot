function toggleTheme() {

    const darkMode =
        document.body.classList.toggle("dark");

    localStorage.setItem(
        "lifepilot-dark",
        darkMode ? "1" : "0"
    );
}


if (
    localStorage.getItem("lifepilot-dark")
    === "1"
) {

    document.body.classList.add("dark");

}
