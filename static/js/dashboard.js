// Create a button to run the pipeline

(async function(url) {
    const response = await fetch(url);
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
})("/languages");

(async function(url) {
    const response = await fetch(url);
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
})("/repos")

// Add more charts