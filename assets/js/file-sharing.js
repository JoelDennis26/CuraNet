// File sharing functionality
class FileSharing {
    constructor() {
        this.currentPatientId = null;
        this.currentDoctorId = null;
    }

    // Upload report file
    async uploadReport(file, patientId, doctorId, sessionId = null, sharedWith = []) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('patient_id', patientId);
        formData.append('doctor_id', doctorId);
        if (sessionId) formData.append('session_id', sessionId);
        formData.append('shared_with', JSON.stringify(sharedWith));

        try {
            const response = await fetch('/reports/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Upload error:', error);
            throw error;
        }
    }

    // Get patient reports
    async getPatientReports(patientId, doctorId) {
        try {
            const response = await fetch(`/reports/patient/${patientId}?doctor_id=${doctorId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch reports');
            }
            return await response.json();
        } catch (error) {
            console.error('Fetch reports error:', error);
            throw error;
        }
    }

    // Download report
    async downloadReport(reportId, doctorId) {
        try {
            const response = await fetch(`/reports/${reportId}/download?doctor_id=${doctorId}`);
            if (!response.ok) {
                throw new Error('Download failed');
            }
            const data = await response.json();
            
            // Open download URL in new tab
            window.open(data.download_url, '_blank');
            return data;
        } catch (error) {
            console.error('Download error:', error);
            throw error;
        }
    }

    // Share report with other doctors
    async shareReport(reportId, doctorIds, currentDoctorId) {
        try {
            const response = await fetch(`/reports/${reportId}/share`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    doctor_ids: doctorIds,
                    current_doctor_id: currentDoctorId
                })
            });

            if (!response.ok) {
                throw new Error('Share failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Share error:', error);
            throw error;
        }
    }

    // Create file upload UI
    createUploadUI(containerId, patientId, doctorId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="file-upload-section">
                <h3>Upload Medical Report</h3>
                <div class="upload-area" id="uploadArea">
                    <input type="file" id="fileInput" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" style="display: none;">
                    <div class="upload-content">
                        <p>Click to select file or drag and drop</p>
                        <small>Supported: PDF, Images, Word documents</small>
                    </div>
                </div>
                <div class="share-options" style="margin-top: 1rem; display: none;" id="shareOptions">
                    <label>Share with doctors:</label>
                    <select multiple id="doctorSelect" class="form-control">
                        <!-- Will be populated dynamically -->
                    </select>
                </div>
                <button id="uploadBtn" class="btn-primary" style="margin-top: 1rem; display: none;">Upload Report</button>
            </div>
        `;

        this.setupUploadEvents(patientId, doctorId);
    }

    // Create reports list UI
    createReportsListUI(containerId, patientId, doctorId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="reports-section">
                <h3>Medical Reports</h3>
                <div id="reportsList" class="reports-list">
                    <p>Loading reports...</p>
                </div>
            </div>
        `;

        this.loadReports(patientId, doctorId);
    }

    // Setup upload event handlers
    setupUploadEvents(patientId, doctorId) {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const shareOptions = document.getElementById('shareOptions');

        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0], patientId, doctorId);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0], patientId, doctorId);
            }
        });

        uploadBtn.addEventListener('click', () => {
            this.handleUpload(patientId, doctorId);
        });
    }

    // Handle file selection
    handleFileSelect(file, patientId, doctorId) {
        const uploadArea = document.getElementById('uploadArea');
        const uploadBtn = document.getElementById('uploadBtn');
        const shareOptions = document.getElementById('shareOptions');

        uploadArea.querySelector('.upload-content').innerHTML = `
            <p><strong>Selected:</strong> ${file.name}</p>
            <small>Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</small>
        `;

        uploadBtn.style.display = 'block';
        shareOptions.style.display = 'block';
        
        this.selectedFile = file;
        this.loadDoctorsList();
    }

    // Handle file upload
    async handleUpload(patientId, doctorId) {
        if (!this.selectedFile) return;

        const uploadBtn = document.getElementById('uploadBtn');
        const doctorSelect = document.getElementById('doctorSelect');
        
        uploadBtn.textContent = 'Uploading...';
        uploadBtn.disabled = true;

        try {
            const sharedWith = Array.from(doctorSelect.selectedOptions).map(option => parseInt(option.value));
            
            await this.uploadReport(this.selectedFile, patientId, doctorId, null, sharedWith);
            
            alert('Report uploaded successfully!');
            this.resetUploadForm();
            this.loadReports(patientId, doctorId);
        } catch (error) {
            alert('Upload failed: ' + error.message);
        } finally {
            uploadBtn.textContent = 'Upload Report';
            uploadBtn.disabled = false;
        }
    }

    // Load doctors list for sharing
    async loadDoctorsList() {
        try {
            const response = await fetch('/api/doctors');
            const doctors = await response.json();
            
            const doctorSelect = document.getElementById('doctorSelect');
            doctorSelect.innerHTML = doctors.map(doctor => 
                `<option value="${doctor.id}">${doctor.name} (${doctor.department})</option>`
            ).join('');
        } catch (error) {
            console.error('Failed to load doctors:', error);
        }
    }

    // Load and display reports
    async loadReports(patientId, doctorId) {
        try {
            const reports = await this.getPatientReports(patientId, doctorId);
            const reportsList = document.getElementById('reportsList');
            
            if (reports.length === 0) {
                reportsList.innerHTML = '<p>No reports found.</p>';
                return;
            }

            reportsList.innerHTML = reports.map(report => `
                <div class="report-item">
                    <div class="report-info">
                        <h4>${report.report_name}</h4>
                        <p>Uploaded by: ${report.uploaded_by}</p>
                        <p>Date: ${new Date(report.uploaded_at).toLocaleDateString()}</p>
                        <p>Size: ${(report.file_size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                    <div class="report-actions">
                        <button class="btn-primary" onclick="fileSharing.downloadReport(${report.report_id}, ${doctorId})">
                            Download
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            document.getElementById('reportsList').innerHTML = '<p>Failed to load reports.</p>';
        }
    }

    // Reset upload form
    resetUploadForm() {
        document.getElementById('uploadArea').querySelector('.upload-content').innerHTML = `
            <p>Click to select file or drag and drop</p>
            <small>Supported: PDF, Images, Word documents</small>
        `;
        document.getElementById('uploadBtn').style.display = 'none';
        document.getElementById('shareOptions').style.display = 'none';
        document.getElementById('fileInput').value = '';
        this.selectedFile = null;
    }
}

// Global instance
const fileSharing = new FileSharing();