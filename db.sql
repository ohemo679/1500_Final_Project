USE school_admissions;

DROP TABLE IF EXISTS test_scores;
DROP TABLE IF EXISTS applicants;

CREATE TABLE applicants (
   id INT AUTO_INCREMENT PRIMARY KEY,
   name VARCHAR(255) NOT NULL,
   contact_address TEXT,
   applied_degree VARCHAR(50) NOT NULL,
   year_applied INT NOT NULL,
   status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending'
);

CREATE TABLE test_scores (
   id INT AUTO_INCREMENT PRIMARY KEY,
   applicant_id INT NOT NULL,
   test_name VARCHAR(50) NOT NULL,
   score INT NOT NULL,
   FOREIGN KEY (applicant_id) REFERENCES applicants(id)
);

ALTER TABLE test_scores 
MODIFY COLUMN test_name ENUM('SAT', 'ACT', 'GRE') NOT NULL;

CREATE INDEX idx_year_applied ON applicants(year_applied);
CREATE INDEX idx_status ON applicants(status);
CREATE INDEX idx_test_scores ON test_scores(applicant_id, test_name);

INSERT INTO applicants (name, contact_address, applied_degree, year_applied, status) VALUES 
('John Smith', '123 Main St, Boston MA', 'Computer Science', 2024, 'pending'),
('Emma Wilson', '456 Park Ave, NYC', 'Engineering', 2024, 'accepted'),
('Michael Brown', '789 Oak Rd, Chicago IL', 'Business', 2024, 'rejected'),
('Sarah Davis', '321 Pine St, SF CA', 'Computer Science', 2024, 'accepted'),
('James Miller', '654 Elm St, Seattle WA', 'Engineering', 2024, 'pending'),
('Lisa Garcia', '987 Cedar Ave, Miami FL', 'Business', 2024, 'accepted'),
('David Lee', '147 Maple Dr, Houston TX', 'Computer Science', 2024, 'pending'),
('Amy Chen', '258 Birch Ln, Portland OR', 'Engineering', 2024, 'accepted'),
('Robert Taylor', '369 Spruce Way, Denver CO', 'Business', 2024, 'rejected'),
('Maria Rodriguez', '741 Ash Blvd, Austin TX', 'Computer Science', 2024, 'accepted');

INSERT INTO test_scores (applicant_id, test_name, score) VALUES
(1, 'SAT', 1450), (1, 'ACT', 32),
(2, 'GRE', 320), (2, 'ACT', 34),
(3, 'GRE', 315), (3, 'ACT', 30),
(4, 'SAT', 1500), (4, 'ACT', 35),
(5, 'GRE', 325), (5, 'ACT', 31),
(6, 'GRE', 318), (6, 'ACT', 33),
(7, 'SAT', 1400), (7, 'ACT', 29),
(8, 'GRE', 330), (8, 'ACT', 34),
(9, 'GRE', 310), (9, 'ACT', 28),
(10, 'SAT', 1550), (10, 'ACT', 36);