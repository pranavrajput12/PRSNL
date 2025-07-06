// Sample data for PRSNL frontend testing

function generateId() {
  return Math.random().toString(36).substr(2, 9);
}

function getRandomDate(start, end) {
  return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
}

const now = new Date();
const threeMonthsAgo = new Date();
threeMonthsAgo.setMonth(now.getMonth() - 3);

export const sampleData = [
  {
    id: generateId(),
    url: "https://www.theverge.com/2024/7/1/ai-ethics-new-framework",
    title: "AI Ethics: A New Framework for Responsible Development",
    summary: "Exploring the latest guidelines for ethical AI development and deployment, focusing on transparency and accountability.",
    tags: ["AI", "Ethics", "Policy", "Tech"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    title: "Never Gonna Give You Up - Rick Astley",
    summary: "The classic music video that continues to surprise and delight.",
    tags: ["Music", "Classic", "Fun"],
    type: "video",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://medium.com/javascript-scene/why-i-use-svelte",
    title: "Why I Use Svelte: A Developer's Perspective",
    summary: "A deep dive into the benefits and unique approach of Svelte for building reactive web applications.",
    tags: ["WebDev", "Svelte", "JavaScript", "Frontend"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://twitter.com/elonmusk/status/1234567890",
    title: "Elon Musk on Mars Colonization",
    summary: "A tweet thread discussing the challenges and future of human colonization on Mars.",
    tags: ["Space", "Elon Musk", "Future", "Science"],
    type: "tweet",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "",
    title: "Meeting Notes: Project Alpha Kickoff",
    summary: "Key decisions and action items from the Project Alpha kickoff meeting. Assignees and deadlines noted.",
    tags: ["Work", "Project Management", "Meeting"],
    type: "note",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.nature.com/articles/s41586-024-07890-x",
    title: "Breakthrough in Fusion Energy Research",
    summary: "Scientists achieve a new milestone in sustainable fusion energy, bringing clean power closer to reality.",
    tags: ["Science", "Energy", "Research"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.figma.com/community/file/123456789",
    title: "Figma UI Kit: Modern Dashboard Design",
    summary: "A comprehensive Figma UI kit for designing modern and intuitive dashboards, with reusable components.",
    tags: ["Design", "UI/UX", "Figma", "Tools"],
    type: "file",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.udemy.com/course/python-for-data-science/",
    title: "Python for Data Science - Complete Course",
    summary: "Learn Python programming for data analysis, visualization, and machine learning with this hands-on course.",
    tags: ["Programming", "Data Science", "Python", "Learning"],
    type: "video",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.nasa.gov/press-release/new-exoplanet-discovery",
    title: "NASA Discovers Potentially Habitable Exoplanet",
    summary: "Astronomers confirm the existence of a new exoplanet within its star's habitable zone, sparking excitement for future exploration.",
    tags: ["Space", "Astronomy", "Discovery", "News"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "",
    title: "Idea Brainstorm: Next Gen Productivity App",
    summary: "Initial ideas and features for a new productivity application, focusing on AI integration and minimalist design.",
    tags: ["Productivity", "Ideas", "AppDev"],
    type: "note",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.smashingmagazine.com/2024/06/css-animations-performance/",
    title: "Optimizing CSS Animations for Web Performance",
    summary: "Tips and tricks for creating smooth and performant CSS animations without sacrificing user experience.",
    tags: ["WebDev", "CSS", "Performance", "Frontend"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882",
    title: "Clean Code: A Handbook of Agile Software Craftsmanship",
    summary: "A foundational book for software developers on writing clean, maintainable, and readable code.",
    tags: ["Programming", "Software Engineering", "Book", "Learning"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.youtube.com/watch?v=some_coding_tutorial",
    title: "React Hooks Tutorial for Beginners",
    summary: "An introductory video tutorial on using React Hooks for state management and side effects in React applications.",
    tags: ["WebDev", "React", "JavaScript", "Tutorial"],
    type: "video",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.wired.com/story/quantum-computing-breakthrough/",
    title: "The Race for Quantum Supremacy Heats Up",
    summary: "Major tech companies and research institutions are pushing the boundaries of quantum computing, vying for computational dominance.",
    tags: ["Tech", "Quantum Computing", "Research", "News"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "",
    title: "Recipe: Spicy Lentil Soup",
    summary: "A hearty and flavorful lentil soup recipe with a kick, perfect for a cold evening.",
    tags: ["Cooking", "Recipe", "Food"],
    type: "note",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.nationalgeographic.com/animals/article/wildlife-photography-tips",
    title: "Tips for Stunning Wildlife Photography",
    summary: "Expert advice on capturing breathtaking wildlife photos, from equipment to field techniques.",
    tags: ["Photography", "Nature", "Hobby"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.coursera.org/learn/machine-learning",
    title: "Machine Learning Specialization - Andrew Ng",
    summary: "The foundational course for anyone looking to get into machine learning, taught by a pioneer in the field.",
    tags: ["AI", "Machine Learning", "Learning", "Course"],
    type: "video",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.behance.net/gallery/123456789/Minimalist-Logo-Designs",
    title: "Minimalist Logo Design Portfolio",
    summary: "A collection of elegant and simple logo designs, showcasing modern branding principles.",
    tags: ["Design", "Branding", "Portfolio"],
    type: "file",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.psychologytoday.com/us/blog/the-power-of-mind/202405/benefits-mindfulness-meditation",
    title: "The Benefits of Mindfulness Meditation",
    summary: "Exploring the scientific evidence behind mindfulness meditation and its positive impact on mental health.",
    tags: ["Wellness", "Mindfulness", "Health"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.freecodecamp.org/news/data-structures-and-algorithms-in-javascript/",
    title: "Data Structures & Algorithms in JavaScript",
    summary: "A comprehensive guide to understanding and implementing fundamental data structures and algorithms using JavaScript.",
    tags: ["Programming", "Algorithms", "JavaScript", "Learning"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.ted.com/talks/the_power_of_vulnerability",
    title: "The Power of Vulnerability - Brené Brown",
    summary: "A powerful TED Talk on the importance of vulnerability and courage in human connection.",
    tags: ["Psychology", "Personal Growth", "TED Talk"],
    type: "video",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "",
    title: "Grocery List for the Week",
    summary: "Weekly grocery list including fresh produce, pantry staples, and meal-specific ingredients.",
    tags: ["Personal", "Shopping", "Organization"],
    type: "note",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.architecturaldigest.com/story/modern-home-design-trends",
    title: "Modern Home Design Trends for 2024",
    summary: "Discover the latest trends in contemporary home architecture and interior design, from sustainable materials to smart home integration.",
    tags: ["Design", "Architecture", "Home"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-equations",
    title: "Quadratic Equations - Khan Academy",
    summary: "An interactive lesson on solving quadratic equations using various methods, with practice problems.",
    tags: ["Learning", "Math", "Education"],
    type: "video",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  },
  {
    id: generateId(),
    url: "https://www.github.com/trending",
    title: "GitHub Trending Repositories",
    summary: "Explore the most popular and rapidly growing open-source projects on GitHub.",
    tags: ["Programming", "Open Source", "GitHub"],
    type: "article",
    createdAt: getRandomDate(threeMonthsAgo, now).toISOString()
  }
];