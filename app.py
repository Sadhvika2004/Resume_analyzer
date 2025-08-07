from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import fitz  # PyMuPDF
import docx
import re
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Comprehensive job-skill mapping dictionary
JOB_SKILL_MAPPING = {
    # Software Development
    'software engineer': ['Python', 'Java', 'C++', 'JavaScript', 'React', 'Node.js', 'SQL', 'Git', 'Docker', 'AWS', 'REST API', 'Agile', 'Testing', 'Data Structures', 'Algorithms'],
    'frontend developer': ['HTML', 'CSS', 'JavaScript', 'React', 'Vue.js', 'Angular', 'TypeScript', 'SASS', 'Webpack', 'Responsive Design', 'UI/UX', 'Accessibility', 'Performance Optimization'],
    'backend developer': ['Python', 'Java', 'Node.js', 'C#', 'SQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'Microservices', 'REST API', 'GraphQL'],
    'data scientist': ['Python', 'R', 'SQL', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn', 'Data Visualization', 'Statistics', 'Big Data', 'Hadoop', 'Spark'],
    'devops engineer': ['Linux', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'Jenkins', 'GitLab CI', 'Terraform', 'Ansible', 'Monitoring', 'Logging', 'Shell Scripting', 'Python', 'Networking'],
    'full stack developer': ['HTML', 'CSS', 'JavaScript', 'React', 'Node.js', 'Python', 'SQL', 'MongoDB', 'Git', 'Docker', 'AWS', 'REST API', 'Agile'],
    'mobile developer': ['Swift', 'Kotlin', 'React Native', 'Flutter', 'Xcode', 'Android Studio', 'Mobile UI/UX', 'App Store', 'Google Play', 'Mobile Testing'],
    
    # Data Analytics
    'data analyst': ['SQL', 'Python', 'R', 'Excel', 'Tableau', 'Power BI', 'Statistics', 'Data Visualization', 'ETL', 'Data Cleaning', 'Business Intelligence', 'A/B Testing', 'Google Analytics'],
    'business analyst': ['SQL', 'Excel', 'Tableau', 'Power BI', 'Business Intelligence', 'Requirements Gathering', 'Process Modeling', 'Stakeholder Management', 'Project Management', 'Agile', 'Scrum'],
    'data engineer': ['Python', 'SQL', 'Hadoop', 'Spark', 'Kafka', 'Airflow', 'ETL', 'Data Warehousing', 'AWS', 'Azure', 'Docker', 'Kubernetes', 'Big Data', 'Data Modeling'],
    'machine learning engineer': ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'MLOps', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'Model Deployment'],
    
    # Marketing
    'digital marketing': ['SEO', 'SEM', 'Google Ads', 'Facebook Ads', 'Social Media Marketing', 'Content Marketing', 'Email Marketing', 'Google Analytics', 'Marketing Automation', 'Conversion Optimization', 'A/B Testing'],
    'content marketing': ['Content Strategy', 'SEO', 'Copywriting', 'Social Media', 'Email Marketing', 'Content Management', 'Analytics', 'Brand Management', 'Creative Writing', 'Video Production'],
    'seo specialist': ['SEO', 'Google Analytics', 'Google Search Console', 'Keyword Research', 'Technical SEO', 'On-Page SEO', 'Off-Page SEO', 'Link Building', 'Content Optimization', 'Local SEO'],
    'social media manager': ['Social Media Marketing', 'Content Creation', 'Community Management', 'Analytics', 'Paid Advertising', 'Brand Management', 'Creative Design', 'Trend Analysis'],
    
    # Finance
    'financial analyst': ['Excel', 'Financial Modeling', 'Valuation', 'Accounting', 'SQL', 'Python', 'R', 'Bloomberg Terminal', 'Risk Management', 'Portfolio Management', 'Financial Analysis'],
    'accountant': ['QuickBooks', 'Excel', 'Accounting', 'Tax Preparation', 'Financial Reporting', 'Audit', 'GAAP', 'Bookkeeping', 'Payroll', 'Financial Analysis'],
    'investment banker': ['Financial Modeling', 'Valuation', 'M&A', 'Excel', 'PowerPoint', 'Financial Analysis', 'Due Diligence', 'Capital Markets', 'Investment Banking', 'Corporate Finance'],
    'risk analyst': ['Risk Management', 'Financial Modeling', 'Statistics', 'Python', 'R', 'SQL', 'Excel', 'Regulatory Compliance', 'Stress Testing', 'Portfolio Analysis'],
    
    # Healthcare
    'nurse': ['Patient Care', 'Clinical Skills', 'Medical Terminology', 'Electronic Health Records', 'CPR', 'Medication Administration', 'Patient Assessment', 'Care Planning', 'Communication', 'Teamwork'],
    'medical assistant': ['Medical Terminology', 'Patient Care', 'Electronic Health Records', 'Vital Signs', 'Phlebotomy', 'Medical Billing', 'Scheduling', 'Communication', 'HIPAA', 'Clinical Skills'],
    'healthcare administrator': ['Healthcare Management', 'Electronic Health Records', 'Medical Billing', 'Healthcare Regulations', 'Leadership', 'Project Management', 'Communication', 'Budget Management', 'Quality Improvement', 'Patient Safety'],
    'pharmacist': ['Pharmacy Practice', 'Medication Management', 'Drug Interactions', 'Patient Counseling', 'Pharmaceutical Calculations', 'Regulatory Compliance', 'Inventory Management', 'Clinical Pharmacy'],
    
    # Design
    'ui designer': ['UI Design', 'UX Design', 'Figma', 'Adobe XD', 'Sketch', 'Prototyping', 'User Research', 'Design Systems', 'Wireframing', 'Visual Design'],
    'graphic designer': ['Adobe Creative Suite', 'Photoshop', 'Illustrator', 'InDesign', 'Typography', 'Color Theory', 'Layout Design', 'Brand Identity', 'Print Design', 'Digital Design'],
    'ux designer': ['User Research', 'UX Design', 'UI Design', 'Prototyping', 'Usability Testing', 'Information Architecture', 'Wireframing', 'User Personas', 'Journey Mapping', 'Design Thinking'],
    
    # Sales
    'sales representative': ['Sales Techniques', 'CRM Software', 'Lead Generation', 'Customer Relationship Management', 'Negotiation', 'Product Knowledge', 'Sales Analytics', 'Cold Calling', 'Account Management'],
    'sales manager': ['Sales Management', 'Team Leadership', 'Sales Strategy', 'CRM Software', 'Sales Analytics', 'Performance Management', 'Training', 'Forecasting', 'Account Management'],
    
    # Education
    'teacher': ['Curriculum Development', 'Lesson Planning', 'Classroom Management', 'Student Assessment', 'Educational Technology', 'Differentiated Instruction', 'Parent Communication', 'Professional Development'],
    'instructional designer': ['Curriculum Design', 'E-learning', 'Instructional Design', 'Learning Management Systems', 'Assessment Design', 'Multimedia Development', 'Adult Learning Theory', 'Project Management'],
    
    # Operations
    'project manager': ['Project Management', 'Agile', 'Scrum', 'Risk Management', 'Stakeholder Management', 'Budget Management', 'Team Leadership', 'Microsoft Project', 'JIRA', 'Communication'],
    'operations manager': ['Operations Management', 'Process Improvement', 'Supply Chain Management', 'Quality Control', 'Team Leadership', 'Budget Management', 'Performance Metrics', 'Strategic Planning'],
    'product manager': ['Product Management', 'Product Strategy', 'Market Research', 'User Research', 'Agile', 'Scrum', 'Data Analysis', 'Stakeholder Management', 'Roadmap Planning', 'A/B Testing']
}

# Domain-specific skill additions
DOMAIN_SKILLS = {
    'software development': ['Programming', 'Software Development', 'Version Control', 'Testing', 'Debugging', 'Code Review', 'Software Architecture'],
    'data analytics': ['Data Analysis', 'Statistical Analysis', 'Data Mining', 'Predictive Analytics', 'Business Intelligence', 'Data Storytelling'],
    'marketing': ['Marketing Strategy', 'Brand Management', 'Customer Acquisition', 'Market Research', 'Campaign Management', 'Marketing Analytics'],
    'finance': ['Financial Analysis', 'Investment Management', 'Risk Assessment', 'Financial Planning', 'Compliance', 'Audit'],
    'healthcare': ['Patient Care', 'Medical Knowledge', 'Healthcare Regulations', 'Clinical Skills', 'Medical Terminology', 'Patient Safety'],
    'design': ['Creative Design', 'Visual Communication', 'User Experience', 'Design Thinking', 'Prototyping', 'Design Systems'],
    'sales': ['Sales Process', 'Customer Relationship', 'Negotiation', 'Lead Generation', 'Sales Analytics', 'Account Management'],
    'education': ['Teaching', 'Curriculum Development', 'Student Assessment', 'Educational Technology', 'Learning Design', 'Classroom Management'],
    'operations': ['Process Management', 'Quality Control', 'Supply Chain', 'Operations Strategy', 'Performance Management', 'Team Leadership']
}

YOUTUBE_API_KEY = 'AIzaSyBk6KmoXVcdeQp3Yn1GbNWLByH5ciqj5Ss'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])

def get_expected_skills(domain, job_title):
    """Get expected skills based on domain and job title with fuzzy matching"""
    job_title_lower = job_title.lower().strip()
    
    # First, try exact match
    if job_title_lower in JOB_SKILL_MAPPING:
        base_skills = JOB_SKILL_MAPPING[job_title_lower]
    else:
        # Try partial matching
        base_skills = []
        for job, skills in JOB_SKILL_MAPPING.items():
            if job_title_lower in job or job in job_title_lower:
                base_skills.extend(skills)
        
        # If no match found, use generic skills based on domain
        if not base_skills:
            domain_lower = domain.lower().strip()
            if domain_lower in DOMAIN_SKILLS:
                base_skills = DOMAIN_SKILLS[domain_lower]
            else:
                # Default generic skills
                base_skills = ['Communication', 'Leadership', 'Problem Solving', 'Teamwork', 'Time Management', 'Analytical Skills']
    
    # Add domain-specific skills
    domain_lower = domain.lower().strip()
    if domain_lower in DOMAIN_SKILLS:
        domain_skills = DOMAIN_SKILLS[domain_lower]
        base_skills.extend([skill for skill in domain_skills if skill not in base_skills])
    
    return list(set(base_skills))  # Remove duplicates

def extract_skills(text, expected_skills):
    """Extract skills from text based on expected skills list"""
    found = set()
    for skill in expected_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found.add(skill)
    return list(found)

def analyze_resume(text, domain, job_title):
    """Analyze resume with dynamic expected skills"""
    expected_skills = get_expected_skills(domain, job_title)
    if not expected_skills:
        return 0, [], [], []
    
    extracted_skills = extract_skills(text, expected_skills)
    ats_score = int((len(extracted_skills) / len(expected_skills)) * 100) if expected_skills else 0
    
    # Handle empty extracted skills
    if not extracted_skills:
        extracted_skills = ['No matching skills found']
        key_strengths = ['None']
    else:
        # Key strengths based on frequency in text
        skill_frequency = {}
        for skill in extracted_skills:
            skill_frequency[skill] = len(re.findall(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE))
        
        key_strengths = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
        key_strengths = [skill for skill, _ in key_strengths]
        
        # Handle empty key strengths
        if not key_strengths:
            key_strengths = ['None']
    
    # Generate recommended skills - prioritize missing skills, then add domain-specific ones
    missing_skills = [skill for skill in expected_skills if skill not in extracted_skills]
    
    # If we have enough missing skills, use those
    if len(missing_skills) >= 3:
        recommended_skills = missing_skills[:3]
    else:
        # If not enough missing skills, add some domain-specific skills that weren't extracted
        recommended_skills = missing_skills.copy()
        
        # Add domain-specific skills that are commonly needed
        domain_lower = domain.lower().strip()
        if domain_lower in DOMAIN_SKILLS:
            domain_skills = DOMAIN_SKILLS[domain_lower]
            for skill in domain_skills:
                if skill not in extracted_skills and skill not in recommended_skills and len(recommended_skills) < 3:
                    recommended_skills.append(skill)
        
        # If still not enough, add some generic professional skills
        generic_skills = ['Communication', 'Leadership', 'Problem Solving', 'Teamwork', 'Time Management', 'Analytical Skills']
        for skill in generic_skills:
            if skill not in extracted_skills and skill not in recommended_skills and len(recommended_skills) < 3:
                recommended_skills.append(skill)
    
    # Ensure we always have at least 3 recommended skills
    if len(recommended_skills) < 3:
        # Add some popular skills for the domain if we still don't have enough
        popular_skills = {
            'software development': ['Python', 'JavaScript', 'Git', 'Docker', 'AWS', 'SQL'],
            'data analytics': ['SQL', 'Python', 'Excel', 'Tableau', 'Statistics', 'Data Visualization'],
            'marketing': ['SEO', 'Social Media Marketing', 'Google Analytics', 'Content Marketing', 'Email Marketing'],
            'finance': ['Excel', 'Financial Modeling', 'Accounting', 'Risk Management', 'Financial Analysis'],
            'healthcare': ['Patient Care', 'Medical Terminology', 'Electronic Health Records', 'Communication', 'Clinical Skills'],
            'design': ['UI Design', 'UX Design', 'Adobe Creative Suite', 'Prototyping', 'User Research'],
            'sales': ['CRM Software', 'Lead Generation', 'Negotiation', 'Sales Analytics', 'Account Management'],
            'education': ['Curriculum Development', 'Classroom Management', 'Student Assessment', 'Educational Technology'],
            'operations': ['Project Management', 'Process Improvement', 'Quality Control', 'Team Leadership']
        }
        
        domain_skills = popular_skills.get(domain_lower, ['Communication', 'Leadership', 'Problem Solving'])
        for skill in domain_skills:
            if skill not in extracted_skills and skill not in recommended_skills and len(recommended_skills) < 3:
                recommended_skills.append(skill)
    
    return ats_score, extracted_skills, key_strengths, recommended_skills

def get_youtube_links(skills):
    """Fetch YouTube videos for recommended skills with fallback handling"""
    links = {}
    for skill in skills:
        try:
            params = {
                'q': f"{skill} tutorial",
                'part': 'snippet',
                'type': 'video',
                'maxResults': 3,
                'key': YOUTUBE_API_KEY
            }
            resp = requests.get('https://www.googleapis.com/youtube/v3/search', params=params)
            
            if resp.status_code == 200:
                items = resp.json().get('items', [])
                if items:
                    links[skill] = [
                        {
                            'title': item['snippet']['title'],
                            'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                        }
                        for item in items if 'videoId' in item.get('id', {})
                    ]
                else:
                    # No videos found for this skill
                    links[skill] = [{'title': 'No videos found for this skill', 'url': '#'}]
            else:
                # API error - add fallback
                links[skill] = [{'title': 'Unable to fetch videos (API error)', 'url': '#'}]
                
        except Exception as e:
            print(f"Error fetching YouTube videos for {skill}: {e}")
            # Add fallback for this skill
            links[skill] = [{'title': 'Unable to fetch videos (connection error)', 'url': '#'}]
    
    return links

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    domain = request.form.get('domain', '').strip()
    job_title = request.form.get('job_title', '').strip()
    
    if not domain or not job_title:
        return jsonify({'error': 'Domain and job title are required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext == 'pdf':
            text = extract_text_from_pdf(filepath)
        elif ext == 'docx':
            text = extract_text_from_docx(filepath)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        ats_score, extracted_skills, key_strengths, recommended_skills = analyze_resume(text, domain, job_title)
        youtube_links = get_youtube_links(recommended_skills)
        
        return jsonify({
            'ats_score': ats_score,
            'extracted_skills': extracted_skills,
            'key_strengths': key_strengths,
            'recommended_skills': recommended_skills,
            'youtube_links': youtube_links,
            'domain': domain,
            'job_title': job_title
        }), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)
