// Create a button to run the pipeline

document.getElementById("run-pipeline").addEventListener("click", async function(event) {
    try {
        const response = await fetch("/etl/run");
        const data = await response.json();
        console.log("Pipeline Started...")
        await loadLanguages();
        await loadRepos();
    } catch(error) {
        console.log("Pipeline failed to start: ", error)
    }
});

async function loadLanguages() {
    const response = await fetch("/languages");
    const data = await response.json();
    const languages = data.map(project => project.language_name)
    const starCount = data.map(project => project.total_stars);

    const languageChart = document.getElementById("languages-bar-chart");
    new Chart(languageChart, {
        type: "bar",
        data: {
            labels: languages, // Languages go in here
            datasets: [
                {
                    label: "Languages",
                    data: starCount
                }
            ]
        }
    })
};

async function loadRepos() {
    const response = await fetch("/repos");
    const data = await response.json();
    const repos = data.map(project => project.repo_name);
    const starsCount = data.map(project => project.total_stars);
    const repoChart = document.getElementById("repos-bar-chart");

    new Chart(repoChart, {
        type: "bar",
        data: {
            labels: repos,
            datasets: [{
                label: "Top 10 repositories",
                data: starsCount,
            }]
        }
    })
};

loadLanguages();
loadRepos();

// Add more charts