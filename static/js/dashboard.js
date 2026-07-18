// Create a button to run the pipeline

let languageCanvasChart;
let repoCanvasChart;
let ownerCanvasChart;
let forkCanvasChart;
let watchersCanvasChart;

const loader = document.getElementById("loader");
const pipelineButton = document.getElementById("run-pipeline");
pipelineButton.addEventListener("click", async function(event) {
    
    try {
        pipelineButton.disabled = true;
        loader.classList.remove("hidden");
        const response = await fetch("/etl/run");
        const data = await response.json();
        if (!response.ok) {
            alert(result.message);
            return;
        }
        console.log("Pipeline Started...")
        await Promise.all([
            loadLanguages(),
            loadRepos(),
            loadOwners(),
            loadForks(),
            loadWatchers()
        ]);
        localStorage.setItem("lastPipelineRun", today);
        pipelineButton.textContent = "Already ran today";
    } catch(error) {
        console.log("Pipeline failed to start: ", error)
        pipelineButton.disabled = false;
    } finally {
        loader.classList.add("hidden");
    }
});

async function loadLanguages() {
    const response = await fetch("/languages");
    const data = await response.json();
    const languages = data.map(project => project.language_name)
    const starCount = data.map(project => project.total_stars);
    const languageChart = document.getElementById("languages-bar-chart");

    if (languageCanvasChart) {
        languageCanvasChart.destroy();
    }
    
    languageCanvasChart = new Chart(languageChart, {
        type: "bar",
        data: {
            labels: languages, // Languages go in here
            datasets: [
                {
                    label: "Stars",
                    data: starCount
                }
            ]
        },
        options:{
            plugins: {
                title: {
                    display: true,
                    text: "Top Languages by Stars"
                }},
            scales:{
                x:{
                    title:{
                        display:true,
                        text:"Language"
                    }},
                y:{
                    title:{
                        display:true,
                        text: "Stars"
                    }}
            }}
    })
};

async function loadRepos() {
    const response = await fetch("/repos");
    const data = await response.json();
    const repos = data.map(project => project.repo_name);
    const starsCount = data.map(project => project.total_stars);
    const repoChart = document.getElementById("repos-bar-chart");

    if (repoCanvasChart) {
        repoCanvasChart.destroy();
    }

    repoCanvasChart = new Chart(repoChart, {
        type: "bar",
        data: {
            labels: repos,
            datasets: [{
                label: "Stars",
                data: starsCount,
            }]
        },
        options:{
            plugins: {
                title: {
                    display: true,
                    text: "Top 10 repositories"
                }},
            scales:{
                x:{
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    },
                    title:{
                        display:true,
                        text: "Repository"
                    }},
                y:{
                    title:{
                        display:true,
                        text: "Stars"
                    }}
            }}
    })
};

async function loadForks() {
    const response = await fetch("/forked_repositories");
    const data = await response.json();
    const repos = data.map(project => project.repo_name);
    const forkCount = data.map(project => project.total_forks);
    const forkChart = document.getElementById("forks-bar-chart");

    if (forkCanvasChart) {
        forkCanvasChart.destroy();
    }

    forkCanvasChart = new Chart(forkChart, {
        type: "bar",
        data: {
            labels: repos,
            datasets: [{
                label:  "Forks",
                data: forkCount,
            }]
        },
        options:{
            plugins: {
                title: {
                    display: true,
                    text: "Top 10 most forked repositories"
                }},
            scales:{
                x:{
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        padding: -3
                    },
                    title:{
                        display:true,
                        text: "Repository"
                    }},
                y:{
                    title:{
                        display:true,
                        text: "Forks"
                    }}
            }}
    })
};

async function loadOwners() {
    const response = await fetch("/owners");
    const data = await response.json();
    const owners = data.map(repo => repo.owner_name);
    const starCount = data.map(repo => repo.total_stars);
    const ownerChart = document.getElementById("owners-bar-chart");

    if (ownerCanvasChart) {
        ownerCanvasChart.destroy();
    }

    ownerCanvasChart = new Chart(ownerChart, {
        type: "bar",
        data: {
            labels: owners,
            datasets: [{
                label: "Stars",
                data: starCount,
            }]
        },
        options:{
            plugins: {
                title: {
                    display: true,
                    text: "Top 10 owners with the most starred repositories"
                }},
            scales:{
                x:{
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    },
                    title:{
                        display:true,
                        text: "Owner"
                    }},
                y:{
                    title:{
                        display:true,
                        text: "Stars"
                    }}
            }}
    })
}

async function loadWatchers() {
    const response = await fetch("/watchers");
    const data = await response.json();
    const repos = data.map(repo => repo.repo_name);
    const watchersCount = data.map(repo => repo.total_watchers);
    const watchersChart = document.getElementById("watchers-bar-chart");

    if (watchersCanvasChart) {
        watchersCanvasChart.destroy();
    }

    watchersCanvasChart = new Chart(watchersChart, {
        type: "bar",
        data: {
            labels: repos,
            datasets: [{
                label: "Watchers",
                data: watchersCount,
            }]
        },
        options:{
            plugins: {
                title: {
                    display: true,
                    text: "Top 10 repositories"
                }},
            scales:{
                x:{
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    },
                    title:{
                        display:true,
                        text: "Repository"
                    }},
                y:{
                    title:{
                        display:true,
                        text: "Watchers"
                    }}
            }}
    })
};

loadLanguages();
loadRepos();
loadOwners();
loadForks();
loadWatchers();

// Add more charts - Mabe