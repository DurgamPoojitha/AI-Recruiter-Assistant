document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('resume-upload');
    const fileNameDisplay = document.getElementById('file-name');
    const defaultText = document.querySelector('.default-text');
    const form = document.getElementById('analyze-form');
    const btnText = document.querySelector('.btn-text');
    const loader = document.getElementById('loader');
    const resultsPanel = document.getElementById('results-panel');
    const analyzeBtn = document.getElementById('analyze-btn');
    const processingSteps = document.getElementById('processing-steps');
    const uploadIcon = document.querySelector('.upload-icon');

    // Update File Name Display on Selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            defaultText.style.display = 'none';
            uploadIcon.style.display = 'none';
            fileNameDisplay.style.display = 'block';
            fileNameDisplay.textContent = e.target.files[0].name;
            
            // Add a subtle success state to the dummy box
            document.querySelector('.file-dummy').style.borderColor = 'var(--success)';
            document.querySelector('.file-dummy').style.background = 'rgba(16, 185, 129, 0.05)';
        } else {
            defaultText.style.display = 'block';
            uploadIcon.style.display = 'block';
            fileNameDisplay.style.display = 'none';
            document.querySelector('.file-dummy').style.borderColor = 'rgba(99, 102, 241, 0.4)';
            document.querySelector('.file-dummy').style.background = 'rgba(9, 9, 11, 0.4)';
        }
    });

    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    async function simulateProcessing() {
        processingSteps.classList.remove('hidden');
        const steps = [
            document.getElementById('step-1'),
            document.getElementById('step-2'),
            document.getElementById('step-3')
        ];
        
        // Reset steps
        steps.forEach(s => {
            s.className = 'step';
            s.querySelector('.step-icon').className = 'step-icon loader-small';
        });

        // Step 1
        steps[0].classList.add('active');
        await sleep(800);
        steps[0].classList.replace('active', 'done');
        
        // Step 2
        steps[1].classList.add('active');
        await sleep(1000);
        steps[1].classList.replace('active', 'done');
        
        // Step 3
        steps[2].classList.add('active');
        // Will finish when API returns
        return steps;
    }

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const resumeFile = fileInput.files[0];
        const jobDescription = document.getElementById('job-description').value;

        if (!resumeFile || !jobDescription.trim()) {
            alert("Please provide both a resume and a job description");
            return;
        }

        // Set Loading State
        btnText.textContent = 'Processing...';
        loader.classList.remove('hidden');
        analyzeBtn.disabled = true;
        resultsPanel.classList.add('hidden');
        
        // Start simulation in parallel with API call
        const stepsPromise = simulateProcessing();

        try {
            const formData = new FormData();
            formData.append('resume', resumeFile);
            formData.append('job_description', jobDescription);

            const response = await fetch('http://localhost:8000/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error("Failed to communicate with the server");
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Wait for at least the visual simulation to reach step 3
            const steps = await stepsPromise;
            steps[2].classList.replace('active', 'done');
            await sleep(400); // slight pause before showing results
            
            processingSteps.classList.add('hidden');
            displayResults(data);

        } catch (error) {
            alert("Error: " + error.message);
            processingSteps.classList.add('hidden');
        } finally {
            // Restore Button State
            btnText.textContent = 'Analyze Match';
            loader.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    });

    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            // easeOutQuart
            const easeProgress = 1 - Math.pow(1 - progress, 4);
            obj.innerHTML = (progress === 1 ? end : (start + (end - start) * easeProgress).toFixed(1)) + '%';
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    function displayResults(data) {
        // Show Overall Score
        const scoreVal = data.match_score;
        const scoreTextEl = document.getElementById('score-text');
        
        // Animate text counter
        animateValue(scoreTextEl, 0, scoreVal, 1500);
        
        const circlePath = document.getElementById('score-circle-path');
        // Colors mapping based on new sleek design
        let color = '#f59e0b'; // warning (yellow)
        if (scoreVal >= 75) color = '#10b981'; // success (green)
        else if (scoreVal < 40) color = '#ef4444'; // danger (red)
        
        circlePath.style.stroke = color;
        // Delay the circle animation slightly for effect
        setTimeout(() => {
            circlePath.style.strokeDasharray = `${scoreVal}, 100`;
        }, 100);

        // Populate Breakdown Metrics
        document.getElementById('semantic-score-val').textContent = data.semantic_score + '%';
        document.getElementById('skill-score-val').textContent = data.skill_match_score + '%';
        document.getElementById('experience-val').textContent = `Resume: ${data.resume_experience} Yrs | JD: ${data.jd_experience} Yrs`;

        // Render Pills
        renderPills('matched-skills', data.matched_skills);
        renderPills('missing-skills', data.missing_skills);

        // Render Recommendations
        const recContainer = document.getElementById('recommendations');
        recContainer.innerHTML = '';
        data.recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.className = 'recommendation-item';
            div.textContent = rec;
            recContainer.appendChild(div);
        });

        // Show Results Panel
        resultsPanel.classList.remove('hidden');
    }

    function renderPills(containerId, items) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        if (items.length === 0) {
            container.innerHTML = '<span class="pill" style="opacity:0.5; background:rgba(255,255,255,0.05); color:var(--text-muted); border:none;">None found</span>';
            return;
        }
        items.forEach(item => {
            const span = document.createElement('span');
            span.className = 'pill';
            span.textContent = item;
            container.appendChild(span);
        });
    }
});
