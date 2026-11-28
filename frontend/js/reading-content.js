// Original and expanded Fleng reading passages.
export const READING_LEVELS = ["A0", "A1", "A2", "B1", "B2"];
export const READINGS = [
  {
    "id": "a0-01",
    "level": "A0",
    "title": "My name is Mia",
    "titleUk": "Мене звати Мія",
    "paragraphs": [
      "My name is Mia. I am ten. I live in Lviv. I have a cat. My cat is black. Its name is Max. I like apples and milk.",
      "My home is near my school. My room is small. It has a bed, a chair and a table. I have a green bag on my chair. My books are in the bag. Max likes my room too. He sleeps on my bed at night. In the morning he sits near the door.",
      "I get up at seven. I wash my face and put on my clothes. I have breakfast with my mum. Mum has tea. I have milk and an apple. Max has his own food. His bowl is on the floor in the kitchen. He drinks water from a small white bowl.",
      "At eight I go to school. My friend is called Lisa. We walk to school together. Lisa has a dog, but I have Max. We like animals. At school I have English and maths. I have a pencil, a pen and a notebook on my desk. I like to draw cats in my notebook.",
      "After school I go home. I do my homework at my table. Max sits on the chair next to me. Then I go outside with Lisa. We play in the garden. We see a little bird in a tree. At six I go inside again. Mum and I have dinner.",
      "In the evening I read a book. Max plays with a small red ball. I put my school bag by the door. I put my shoes under the chair. At nine I go to bed. Max is tired too. He comes to my room and lies down. I say good night to Mum and Max.",
      "On Saturday I visit my grandma. She lives near us. I take a picture of Max with me. Grandma has a white cat. Its name is Snow. I like Snow too."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "How old is Mia?",
        "options": [
          "Eight",
          "Twelve",
          "Ten"
        ],
        "answer": 2,
        "evidence": "I am ten."
      },
      {
        "type": "choice",
        "prompt": "Where does Mia live?",
        "options": [
          "London",
          "Lviv",
          "Kyiv"
        ],
        "answer": 1,
        "evidence": "I live in Lviv."
      },
      {
        "type": "choice",
        "prompt": "What is the cat’s name?",
        "options": [
          "Max",
          "Mia",
          "Tom"
        ],
        "answer": 0,
        "evidence": "Its name is Max."
      },
      {
        "type": "true_false",
        "prompt": "The cat is black.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "My cat is black."
      },
      {
        "type": "true_false",
        "prompt": "Mia likes bananas and tea.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "I like apples and milk."
      },
      {
        "type": "choice",
        "prompt": "Where does Max sleep at night?",
        "options": [
          "On Mia's bed",
          "In the garden",
          "Under the kitchen table"
        ],
        "answer": 0,
        "evidence": "He sleeps on my bed at night."
      },
      {
        "type": "choice",
        "prompt": "What colour is Mia's school bag?",
        "options": [
          "Red",
          "Blue",
          "Green"
        ],
        "answer": 2,
        "evidence": "I have a green bag on my chair."
      },
      {
        "type": "choice",
        "prompt": "What is Grandma's cat called?",
        "options": [
          "Max",
          "Snow",
          "Pip"
        ],
        "answer": 1,
        "evidence": "Its name is Snow."
      },
      {
        "type": "true_false",
        "prompt": "Mia goes to bed at nine.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "At nine I go to bed."
      },
      {
        "type": "true_false",
        "prompt": "Grandma has a black cat.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Grandma has a white cat."
      }
    ]
  },
  {
    "id": "a0-02",
    "level": "A0",
    "title": "At school",
    "titleUk": "У школі",
    "paragraphs": [
      "This is my school. My bag is blue. I have two pens and one book. My teacher is Anna. I sit next to Ben. We read and write.",
      "I go to school at eight. My school is near my home. There are many rooms in the school. My classroom has a door and two big windows. There is a clock on the wall. There are ten desks. My desk is near the window. I can see a tree outside.",
      "Anna comes into the room. We say hello. She says good morning. We open our books. Anna writes a word on the board. I write the word in my book. Ben has a pencil. He draws a house. I draw a cat. Anna looks at our pictures and smiles.",
      "At ten we have a break. I have a banana in my bag. Ben has a sandwich. We eat in the school yard. We see our friends. They have a ball. We play with them. Then the bell rings. We go back to our classroom.",
      "In English class we read a short story. There is a girl and a dog in the story. Anna asks a question. I know the answer. Ben asks me for a pen. I give him my second pen. We help each other. After English we have maths. We write numbers on the board.",
      "At one we have lunch. I drink water and eat some rice. After lunch we have art. I use a red pencil and a blue pencil. At three I close my book and put it in my bag. I say goodbye to Anna and Ben. I walk home with my sister. At home I show Mum my picture.",
      "I put my picture on the wall at home. Mum likes it. I take a new piece of paper and draw another picture for Ben."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What colour is the bag?",
        "options": [
          "Green",
          "Blue",
          "Red"
        ],
        "answer": 1,
        "evidence": "My bag is blue."
      },
      {
        "type": "true_false",
        "prompt": "The student sits next to Anna.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "I sit next to Ben."
      },
      {
        "type": "choice",
        "prompt": "How many pens are there?",
        "options": [
          "Two",
          "One",
          "Three"
        ],
        "answer": 0,
        "evidence": "I have two pens and one book."
      },
      {
        "type": "choice",
        "prompt": "Who is the teacher?",
        "options": [
          "Ben",
          "Max",
          "Anna"
        ],
        "answer": 2,
        "evidence": "My teacher is Anna."
      },
      {
        "type": "true_false",
        "prompt": "The student has one book.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "I have two pens and one book."
      },
      {
        "type": "choice",
        "prompt": "How many desks are in the classroom?",
        "options": [
          "Two",
          "Six",
          "Ten"
        ],
        "answer": 2,
        "evidence": "There are ten desks."
      },
      {
        "type": "choice",
        "prompt": "What does Ben draw?",
        "options": [
          "A cat",
          "A house",
          "A dog"
        ],
        "answer": 1,
        "evidence": "He draws a house."
      },
      {
        "type": "choice",
        "prompt": "Where does the narrator put the school picture?",
        "options": [
          "In the teacher's bag",
          "On the school desk",
          "On the wall at home"
        ],
        "answer": 2,
        "evidence": "I put my picture on the wall at home."
      },
      {
        "type": "true_false",
        "prompt": "The narrator has a banana at break time.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "I have a banana in my bag."
      },
      {
        "type": "true_false",
        "prompt": "The narrator draws another picture for Anna.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "I take a new piece of paper and draw another picture for Ben."
      }
    ]
  },
  {
    "id": "a0-03",
    "level": "A0",
    "title": "My family",
    "titleUk": "Моя сім’я",
    "paragraphs": [
      "I am Leo. I live with my mum, dad and sister. My sister is six. Her name is Eva. Dad has a red car. Mum likes music. We have a small dog.",
      "Our house is not big. We have a kitchen, a living room and three bedrooms. My bedroom is next to Eva's room. Eva has a pink chair and many toys. I have a blue chair and some books. Our dog sleeps in the living room. His name is Pip.",
      "In the morning Dad makes breakfast. He eats bread and cheese. Eva likes milk. I like eggs. Mum puts food in Pip's bowl. We sit at the table together. Eva talks a lot. Dad listens and smiles. Then we put our cups in the kitchen.",
      "Dad drives to work in his car. Mum walks to work. Eva and I go to school. Eva is in a small class. I am in a big class. At school I have friends. Eva has a friend called Lily. We see them in the school yard at lunch.",
      "In the afternoon we come home. I help Eva with her book. She can read some words. We play with Pip in the garden. Pip runs after a ball. Eva throws the ball and I catch it. Mum comes home at five. She puts on some music in the kitchen.",
      "On Sunday we stay at home. Dad cleans his car. Mum makes soup. Eva and I put the plates on the table. After lunch we walk to the park. Pip comes with us. Dad holds Pip's lead. Eva sees a bird and points at it. In the evening we sit together and look at a family photo. I love my family.",
      "On Monday Eva takes a photo of Pip to school. I have a photo of our family in my book. I look at it at lunch. After school we go home together. Dad is at home when we arrive. We play with Pip."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Who is six?",
        "options": [
          "Eva",
          "Leo",
          "Mum"
        ],
        "answer": 0,
        "evidence": "My sister is six. Her name is Eva."
      },
      {
        "type": "choice",
        "prompt": "What colour is Dad’s car?",
        "options": [
          "Blue",
          "White",
          "Red"
        ],
        "answer": 2,
        "evidence": "Dad has a red car."
      },
      {
        "type": "choice",
        "prompt": "What does Mum like?",
        "options": [
          "Art",
          "Music",
          "Football"
        ],
        "answer": 1,
        "evidence": "Mum likes music."
      },
      {
        "type": "true_false",
        "prompt": "The family has a small dog.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "We have a small dog."
      },
      {
        "type": "true_false",
        "prompt": "Leo lives with his brother.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "I live with my mum, dad and sister."
      },
      {
        "type": "choice",
        "prompt": "What is the dog's name?",
        "options": [
          "Ben",
          "Pip",
          "Leo"
        ],
        "answer": 1,
        "evidence": "His name is Pip."
      },
      {
        "type": "choice",
        "prompt": "What does Leo's dad eat for breakfast?",
        "options": [
          "Bread and cheese",
          "Eggs and apples",
          "Rice and fish"
        ],
        "answer": 0,
        "evidence": "He eats bread and cheese."
      },
      {
        "type": "choice",
        "prompt": "What does Eva take to school on Monday?",
        "options": [
          "A ball",
          "A photo of Pip",
          "A toy car"
        ],
        "answer": 1,
        "evidence": "On Monday Eva takes a photo of Pip to school."
      },
      {
        "type": "true_false",
        "prompt": "Eva has a pink chair.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Eva has a pink chair and many toys."
      },
      {
        "type": "true_false",
        "prompt": "Dad is away when the children arrive home on Monday.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Dad is at home when we arrive."
      }
    ]
  },
  {
    "id": "a0-04",
    "level": "A0",
    "title": "A good breakfast",
    "titleUk": "Гарний сніданок",
    "paragraphs": [
      "It is seven. I am in the kitchen. I eat bread and an egg. I drink water. My brother eats an apple. He drinks milk. We go to school at eight.",
      "My mum is in the kitchen too. She makes breakfast for us. There are four plates on the table. My plate is white. My brother has a blue plate. Mum puts two cups near the plates. There is a big bottle of water on the table.",
      "I like my egg. It is warm. I put some bread on my plate. My brother has a red apple. He cuts the apple into small pieces. He gives me one piece. I give him a little bread. We say thank you. Mum has tea and some cheese.",
      "After breakfast we take our plates to the sink. I wash my cup. My brother puts the milk in the fridge. We clean the table. Mum puts a sandwich in my bag. She puts an orange in my brother's bag. The food is for lunch at school.",
      "At school I sit next to my friend. At twelve we have lunch. I eat my sandwich and drink water. My friend has an apple. We talk about our breakfast. She likes bananas. My brother is in another class. I see him in the yard.",
      "On Sunday we do not go to school. We eat breakfast at nine. I help Mum in the kitchen. We have bread, eggs, tomatoes and fruit. Dad makes tea. My brother puts the cups on the table. After breakfast we read or play. I like breakfast with my family. It is a nice start to the day.",
      "In the shop near our home there are many kinds of bread. On Saturday Mum and I go to the shop. She buys brown bread and six eggs. I carry the bread in a bag. We take it home and put it on the table."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Where is the speaker?",
        "options": [
          "In the garden",
          "At school",
          "In the kitchen"
        ],
        "answer": 2,
        "evidence": "I am in the kitchen."
      },
      {
        "type": "choice",
        "prompt": "What does the brother drink?",
        "options": [
          "Tea",
          "Milk",
          "Water"
        ],
        "answer": 1,
        "evidence": "He drinks milk."
      },
      {
        "type": "choice",
        "prompt": "When do they go to school?",
        "options": [
          "At eight",
          "At seven",
          "At nine"
        ],
        "answer": 0,
        "evidence": "We go to school at eight."
      },
      {
        "type": "true_false",
        "prompt": "The brother eats a banana.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "My brother eats an apple."
      },
      {
        "type": "true_false",
        "prompt": "The speaker eats an egg.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "I eat bread and an egg."
      },
      {
        "type": "choice",
        "prompt": "What colour is the brother's plate?",
        "options": [
          "Blue",
          "White",
          "Green"
        ],
        "answer": 0,
        "evidence": "My brother has a blue plate."
      },
      {
        "type": "choice",
        "prompt": "What does Mum put in the narrator's school bag?",
        "options": [
          "A book",
          "An orange",
          "A sandwich"
        ],
        "answer": 2,
        "evidence": "Mum puts a sandwich in my bag."
      },
      {
        "type": "choice",
        "prompt": "What bread does Mum buy on Saturday?",
        "options": [
          "White bread",
          "Brown bread",
          "No bread"
        ],
        "answer": 1,
        "evidence": "She buys brown bread and six eggs."
      },
      {
        "type": "true_false",
        "prompt": "The brother puts the milk in the fridge.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "My brother puts the milk in the fridge."
      },
      {
        "type": "true_false",
        "prompt": "Mum buys two eggs on Saturday.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "She buys brown bread and six eggs."
      }
    ]
  },
  {
    "id": "a0-05",
    "level": "A0",
    "title": "My room",
    "titleUk": "Моя кімната",
    "paragraphs": [
      "This is my room. There is a bed and a desk. My book is on the desk. My shoes are under the bed. The window is big. I have a yellow lamp.",
      "I like my room. The walls are white. The floor is brown. My bed is next to the wall. There is a blue blanket on it. There are two pillows. My desk is near the window. I have a small chair at my desk.",
      "On the desk there is a book, a pen and a cup. My pencils are in the cup. The lamp is next to the cup. I use the lamp in the evening. There is a photo of my family on the wall. There is a clock near the photo.",
      "I have a box under the desk. My toys are in the box. There is a red car and a small bear in it. My clothes are in a cupboard. My school bag is by the door. I put my books in the bag every evening.",
      "In the morning I open the window. I make my bed. I put my shoes on and go to the kitchen. After school I come back to my room. I sit at my desk and read. My friend comes to my house on Friday. We sit on the floor and play a game.",
      "On Saturday I clean my room. I put my toys in the box. I put my books on a shelf. I put my shoes in the right place. Mum helps me with the window. Then I sit on my bed and look at a picture book. The room is clean and I am happy. It is my favourite place at home.",
      "My friend has a small room too. His desk is next to his bed. He has no lamp on his desk. We draw a picture of our rooms. I put my picture in my book."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Where is the book?",
        "options": [
          "On the chair",
          "On the desk",
          "Under the bed"
        ],
        "answer": 1,
        "evidence": "My book is on the desk."
      },
      {
        "type": "true_false",
        "prompt": "The window is big.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "The window is big."
      },
      {
        "type": "choice",
        "prompt": "What is under the bed?",
        "options": [
          "Shoes",
          "A book",
          "A lamp"
        ],
        "answer": 0,
        "evidence": "My shoes are under the bed."
      },
      {
        "type": "choice",
        "prompt": "What colour is the lamp?",
        "options": [
          "Black",
          "Blue",
          "Yellow"
        ],
        "answer": 2,
        "evidence": "I have a yellow lamp."
      },
      {
        "type": "true_false",
        "prompt": "There are two beds.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "There is a bed and a desk."
      },
      {
        "type": "choice",
        "prompt": "What colour is the blanket?",
        "options": [
          "Yellow",
          "Red",
          "Blue"
        ],
        "answer": 2,
        "evidence": "There is a blue blanket on it."
      },
      {
        "type": "choice",
        "prompt": "Where are the pencils?",
        "options": [
          "Under the bed",
          "In a cup",
          "In the cupboard"
        ],
        "answer": 1,
        "evidence": "My pencils are in the cup."
      },
      {
        "type": "choice",
        "prompt": "Where is the friend's desk?",
        "options": [
          "Under his window",
          "By his door",
          "Next to his bed"
        ],
        "answer": 2,
        "evidence": "His desk is next to his bed."
      },
      {
        "type": "true_false",
        "prompt": "The school bag is by the door.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "My school bag is by the door."
      },
      {
        "type": "true_false",
        "prompt": "The friend has a lamp on his desk.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "He has no lamp on his desk."
      }
    ]
  },
  {
    "id": "a0-06",
    "level": "A0",
    "title": "At the park",
    "titleUk": "У парку",
    "paragraphs": [
      "I am at the park with Tom. It is sunny. Tom has a ball. I have a bike. We see three ducks. The ducks are in the water. We are happy.",
      "The park is near our houses. We go there in the morning. Tom wears a green shirt. I wear a blue shirt. We have water in our bags. There are many trees in the park. There are flowers near the gate. We see a man with a small dog.",
      "We walk to the grass. Tom puts his bag on a bench. We play with his ball. He throws it and I catch it. Then I ride my bike on the path. Tom walks next to me. We stop near a big tree. We sit in the shade and drink water.",
      "There is a lake in the park. We go to the lake. We look at the ducks from the path. One duck is near the grass. Two ducks swim together. There are birds in the trees too. Tom takes a photo of the lake. I look at the flowers.",
      "At twelve we have lunch. I have a cheese sandwich. Tom has two apples and some bread. We sit on a bench. We put our paper in a bin. A little girl plays with her dad near us. We say hello to them. Then we play another game.",
      "In the afternoon we go home. I put my bike in the garage. Tom takes his ball home. I tell my mum about the ducks and the flowers. She likes the park too. We want to go there again on Sunday. I put my empty water bottle in the kitchen and wash my hands.",
      "At home Tom calls me. He wants to go to the park with his sister next time. I say yes. We can take a ball and some food. We put the park on our plan for Sunday."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Who has a ball?",
        "options": [
          "Tom",
          "The speaker",
          "A girl"
        ],
        "answer": 0,
        "evidence": "Tom has a ball."
      },
      {
        "type": "choice",
        "prompt": "How many ducks are there?",
        "options": [
          "Two",
          "Four",
          "Three"
        ],
        "answer": 2,
        "evidence": "We see three ducks."
      },
      {
        "type": "choice",
        "prompt": "Where are the ducks?",
        "options": [
          "On a bike",
          "In the water",
          "In a tree"
        ],
        "answer": 1,
        "evidence": "The ducks are in the water."
      },
      {
        "type": "true_false",
        "prompt": "The speaker has a car.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "I have a bike."
      },
      {
        "type": "true_false",
        "prompt": "It is sunny.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "It is sunny."
      },
      {
        "type": "choice",
        "prompt": "Where does Tom put his bag?",
        "options": [
          "On his bike",
          "On a bench",
          "In a tree"
        ],
        "answer": 1,
        "evidence": "Tom puts his bag on a bench."
      },
      {
        "type": "choice",
        "prompt": "What does Tom take a photo of?",
        "options": [
          "The lake",
          "The dog",
          "The gate"
        ],
        "answer": 0,
        "evidence": "Tom takes a photo of the lake."
      },
      {
        "type": "choice",
        "prompt": "Who does Tom want to bring to the park next time?",
        "options": [
          "His sister",
          "His dad",
          "His mum"
        ],
        "answer": 0,
        "evidence": "He wants to go to the park with his sister next time."
      },
      {
        "type": "true_false",
        "prompt": "They drink water in the shade.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "We sit in the shade and drink water."
      },
      {
        "type": "true_false",
        "prompt": "They plan to return on Monday.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "We put the park on our plan for Sunday."
      }
    ]
  },
  {
    "id": "a1-01",
    "level": "A1",
    "title": "A Saturday at the market",
    "titleUk": "Субота на ринку",
    "paragraphs": [
      "Every Saturday, Nina goes to the market with her father. They leave home at nine and walk for ten minutes. Nina buys strawberries and her father buys vegetables for soup. They usually stop at a small bakery on the way home. Today the bakery is closed, so they make sandwiches at home instead. Nina enjoys shopping with her father because they can talk and spend time together.",
      "Before they leave, Nina and her father look in the fridge. They have enough milk and eggs, but they need fresh food for the weekend. Her father writes a short list on a piece of paper. Nina takes two cloth bags from a cupboard. She likes carrying the bags because they are easy to use again.",
      "The market is in a square near the bus station. There are many tables with fruit, vegetables, bread and flowers. Some sellers know Nina's father by name. At the first table, they buy six potatoes and a bag of carrots. Nina asks if she can choose the tomatoes. She picks the red ones that feel firm, and her father shows her how to put them in the bag without hurting them.",
      "Next they visit a woman who sells fruit from her garden. Nina wants strawberries for dessert. The woman lets her try one. It is sweet, so Nina buys a small box. She pays for it herself and counts the change. Her father has given her enough money for the fruit and a little extra for a snack.",
      "They also look at the flower stall. Nina sees some yellow flowers that her mother would like. She asks her father to buy a small bunch. They put the flowers at the top of a bag, away from the heavy vegetables. They still have to buy onions for the soup, so they return to another stall near the entrance.",
      "On the way home, they stop to look at a notice on the bakery door. It says that the shop will open again on Tuesday. Nina is a little disappointed because she wanted a warm roll, but her father has another idea. They have some bread and cheese at home. They can make lunch together instead of buying something outside.",
      "At home they wash the vegetables and put the fruit in the fridge. Nina makes sandwiches while her father begins to prepare soup for dinner. She uses cheese, tomato and a little butter. They sit at the kitchen table and eat their lunch. Her mother comes home later and finds the flowers in a glass of water. She is very pleased.",
      "Nina tells her mother about the woman at the fruit stall. She also says that she wants to buy something by herself next week. Her father agrees to let her do more of the shopping. They decide to make a list together every Friday evening. Nina is learning how much things cost and how to choose fresh food. For her, the market is not only a place to buy things. It is a place where she learns something new and sees people she knows.",
      "The following Friday, Nina and her father make their new shopping list. They first look at the food they have left. There are two carrots, three eggs and a little cheese. They write down the things they really need. Nina suggests taking a smaller bag this time because they do not have to buy so many vegetables. Her father puts some coins in her purse and asks her to keep them separate from his money.",
      "At the market the next morning, Nina goes to the fruit stall and asks how much a box of apples costs. She listens to the price before taking out her money. She notices that the seller has put the prices on small signs. The apples are a little more expensive than she expected, so she chooses a smaller box. Her father says that this is a sensible choice. They buy fresh rolls when they find that the bakery is open again. On the way home, Nina tells her father that she feels more confident about shopping. She wants to choose the fruit for their family picnic next month."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "How do they get to the market?",
        "options": [
          "By bus",
          "By car",
          "On foot"
        ],
        "answer": 2,
        "evidence": "They leave home at nine and walk for ten minutes."
      },
      {
        "type": "choice",
        "prompt": "What does Nina buy?",
        "options": [
          "Sandwiches",
          "Strawberries",
          "Vegetables"
        ],
        "answer": 1,
        "evidence": "Nina buys strawberries."
      },
      {
        "type": "choice",
        "prompt": "Why do they make sandwiches today?",
        "options": [
          "The bakery is closed.",
          "They missed the market.",
          "Her father dislikes bread."
        ],
        "answer": 0,
        "evidence": "Today the bakery is closed, so they make sandwiches at home instead."
      },
      {
        "type": "true_false",
        "prompt": "They go to the market every Saturday.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Every Saturday, Nina goes to the market with her father."
      },
      {
        "type": "true_false",
        "prompt": "The walk takes thirty minutes.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "They walk for ten minutes."
      },
      {
        "type": "choice",
        "prompt": "What does Nina take from the cupboard before leaving?",
        "options": [
          "Two cloth bags",
          "A lunch box",
          "A basket of apples"
        ],
        "answer": 0,
        "evidence": "Nina takes two cloth bags from a cupboard."
      },
      {
        "type": "choice",
        "prompt": "Why does Nina buy a box of strawberries?",
        "options": [
          "Her father needs them for soup",
          "They are cheaper than bread",
          "She tries one and likes the taste"
        ],
        "answer": 2,
        "evidence": "It is sweet, so Nina buys a small box."
      },
      {
        "type": "choice",
        "prompt": "What does Nina choose for the next shopping trip?",
        "options": [
          "A smaller box of apples",
          "A box of strawberries for soup",
          "A large bag of potatoes"
        ],
        "answer": 0,
        "evidence": "The apples are a little more expensive than she expected, so she chooses a smaller box."
      },
      {
        "type": "true_false",
        "prompt": "Nina pays for the strawberries herself.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "She pays for it herself and counts the change."
      },
      {
        "type": "true_false",
        "prompt": "The bakery remains closed the following Saturday.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "They buy fresh rolls when they find that the bakery is open again."
      }
    ]
  },
  {
    "id": "a1-02",
    "level": "A1",
    "title": "The new student",
    "titleUk": "Новий учень",
    "paragraphs": [
      "On Monday, a new student joins Mark’s class. His name is Adam and he is from Poland. He speaks Polish and a little English. At lunch, Mark asks Adam to sit with his friends. They talk about football and find out that they both play on Sundays. After school, Mark shows Adam the library and the sports hall. Adam is happy because he already has a friend at his new school.",
      "Before the first lesson, their teacher writes Adam's name on the board and asks everyone to introduce themselves. Adam is quiet at first. He understands some of the questions but needs a little time to answer them. Mark tells him his own name and points to a free chair. Adam puts his bag under the desk and takes out a notebook.",
      "In English class, the teacher asks the students to work in pairs. Mark and Adam read a short conversation together. Adam knows the names of many animals, but he does not know the word for a school subject. Mark shows him a picture in the book. Adam teaches Mark how to say hello in Polish. They both laugh when Mark tries to say it for the first time.",
      "At the lunch table, two other friends ask Adam about his old school. He tells them that his family moved last month. He misses his old friends, but he likes the new town. One of the students, Sara, asks him about his favourite sport. He says that he likes playing football more than watching it. Mark invites him to join their game on the weekend.",
      "After lunch, the class has art. Everyone has to make a picture of a place they know well. Adam draws a park near his old home. Mark draws the school sports field. When the teacher looks at the pictures, she asks Adam to tell the class something about his park. He uses a few English words and points to the picture when he cannot find the right word.",
      "At the end of the day, Mark shows Adam where to find books in the library. The librarian gives Adam a card and explains when he can take books home. Then the two boys walk to the sports hall. A group of students is playing basketball inside, but the football club meets outside on Wednesdays.",
      "The next morning, Adam arrives a little earlier. He knows where the classroom is now and does not need to wait for the teacher at the entrance. He brings a small dictionary in his bag. Mark asks him to sit with him again. During the break, Adam tells Mark that he has written the new football words in his notebook.",
      "On Sunday, Adam joins the football game. He passes the ball to Sara and helps Mark score a goal. They do not keep a score because they are playing for fun. After the game, they sit on a bench and talk. Adam still needs time to learn English, but he is not afraid to ask questions. Mark knows that a new school can feel strange. He is glad that a simple invitation at lunch helped someone feel welcome.",
      "A few weeks later, Adam knows more people at school. He still finds some lessons difficult, especially when the teacher speaks quickly. He has started to write new words on small cards. On one side he writes the English word, and on the other side he writes the Polish word. He reads the cards when he has a few free minutes. Mark offers to practise English with him during lunch, but Adam also wants to spend time talking about things that are not schoolwork.",
      "Their teacher notices that the two boys are becoming friends. She asks the class to prepare a short presentation about a place they like. Adam chooses a town in Poland and brings some pictures from home. Mark helps him with a few English sentences, but Adam gives the presentation himself. After the lesson, several students ask him questions about the town. Adam is happy that they are interested in his country. He begins to understand that he can share something with his classmates even while he is still learning their language. He decides to join the school football club and invites Mark to go with him on Wednesday."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Where is Adam from?",
        "options": [
          "Ukraine",
          "Poland",
          "Spain"
        ],
        "answer": 1,
        "evidence": "He is from Poland."
      },
      {
        "type": "true_false",
        "prompt": "Adam speaks only English.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "He speaks Polish and a little English."
      },
      {
        "type": "choice",
        "prompt": "What sport do both boys play?",
        "options": [
          "Football",
          "Basketball",
          "Tennis"
        ],
        "answer": 0,
        "evidence": "They talk about football and find out that they both play on Sundays."
      },
      {
        "type": "choice",
        "prompt": "What does Mark show Adam?",
        "options": [
          "The kitchen and garden",
          "The bus stop and shop",
          "The library and sports hall"
        ],
        "answer": 2,
        "evidence": "Mark shows Adam the library and the sports hall."
      },
      {
        "type": "true_false",
        "prompt": "Adam joins the class on Monday.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "On Monday, a new student joins Mark’s class."
      },
      {
        "type": "choice",
        "prompt": "What does Mark show Adam when he cannot find an English word?",
        "options": [
          "A video on his phone",
          "A map of the town",
          "A picture in the book"
        ],
        "answer": 2,
        "evidence": "Mark shows him a picture in the book."
      },
      {
        "type": "choice",
        "prompt": "What does Adam draw in art class?",
        "options": [
          "The sports hall",
          "A park near his old home",
          "The school library"
        ],
        "answer": 1,
        "evidence": "Adam draws a park near his old home."
      },
      {
        "type": "choice",
        "prompt": "What does Adam use to practise vocabulary?",
        "options": [
          "Small cards",
          "A football programme",
          "A large poster"
        ],
        "answer": 0,
        "evidence": "He has started to write new words on small cards."
      },
      {
        "type": "true_false",
        "prompt": "Adam teaches Mark how to say hello in Polish.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Adam teaches Mark how to say hello in Polish."
      },
      {
        "type": "true_false",
        "prompt": "Mark gives Adam's presentation for him.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Mark helps him with a few English sentences, but Adam gives the presentation himself."
      }
    ]
  },
  {
    "id": "a1-03",
    "level": "A1",
    "title": "A rainy afternoon",
    "titleUk": "Дощовий день",
    "paragraphs": [
      "Lily wants to ride her bike after school, but it starts to rain. She puts her bike in the garage and goes inside. Her grandmother is making cookies. Lily helps her mix the flour and sugar. While the cookies are in the oven, they play a game of cards. When the rain stops, it is nearly six o’clock. Lily decides to ride her bike tomorrow instead.",
      "Lily was looking forward to the afternoon because she had a new bell on her bike. She wanted to show it to her friend Ellie. When she sees the dark clouds outside, she sends Ellie a message to say that they cannot meet in the park. Ellie writes back and suggests meeting the following day.",
      "In the kitchen, Grandmother asks Lily to wash her hands. She puts a large bowl on the table and gives Lily a spoon. They need flour, sugar, butter and an egg. Lily reads the recipe aloud. Her grandmother measures the ingredients, and Lily mixes them. The mixture is a little dry, so they add the egg carefully.",
      "Grandmother shows Lily how to make small round cookies. They put the cookies on a tray and leave space between them. Lily counts twenty cookies. Some are bigger than others. Grandmother says that it is fine if they are not all the same shape. Lily makes one cookie in the shape of a heart for her mother.",
      "While the cookies bake, Lily looks out of the window. Rain runs down the glass and the garden path is wet. Her grandmother brings a pack of cards to the table. She teaches Lily a game that she used to play with her brother when she was young. Lily loses the first game but wins the second one. They decide to play a third game after the cookies are ready.",
      "Soon there is a lovely smell in the kitchen. Grandmother takes the tray out of the oven and puts it in a safe place. They wait until the cookies are cool enough to eat. Lily makes two cups of tea with her grandmother's help. They put some cookies on a plate and save the others in a tin for the rest of the family.",
      "At about six, the clouds begin to move away. Lily can see a little sunshine, but there are still large puddles outside. She checks her bike in the garage and makes sure it is dry. She decides not to hurry. Tomorrow she will have more time to ride with Ellie.",
      "In the evening, Lily's mother arrives home and tries the heart-shaped cookie. She asks Lily how her afternoon was. Lily says that the rain changed her plans, but she had a good time anyway. She writes the cookie recipe in her notebook so she can make them again. She also asks her grandmother to teach her another card game next weekend. A rainy day can be a good day when there is something enjoyable to do indoors.",
      "The next morning, Lily looks out of the window as soon as she wakes up. The sky is clear and the garden is dry in most places. She eats breakfast and puts a bottle of water in her bag. Her mother reminds her to wear her helmet. Lily checks that the bell on her bike works and that her tyres have enough air. Then she sends Ellie a message and asks if she is ready to meet.",
      "The girls ride slowly along the path because some puddles are still there. Lily shows Ellie the new bell. They stop for a rest near a tree and eat two cookies that Lily has brought from home. Ellie asks where the cookies came from. Lily tells her about the afternoon with her grandmother and the card game they played. She suggests making cookies together the next time it rains. When Lily goes home, she puts her bike away and tells Grandmother that the cookies were very good after the ride. She is glad that she was able to enjoy both days, even though they were very different."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Why does Lily stay inside?",
        "options": [
          "It starts to rain.",
          "Her bike is broken.",
          "She has a test."
        ],
        "answer": 0,
        "evidence": "It starts to rain."
      },
      {
        "type": "choice",
        "prompt": "What is her grandmother making?",
        "options": [
          "Soup",
          "Salad",
          "Cookies"
        ],
        "answer": 2,
        "evidence": "Her grandmother is making cookies."
      },
      {
        "type": "choice",
        "prompt": "What do they do while they wait?",
        "options": [
          "Ride bikes",
          "Play cards",
          "Watch TV"
        ],
        "answer": 1,
        "evidence": "They play a game of cards."
      },
      {
        "type": "true_false",
        "prompt": "Lily puts her bike in the garage.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "She puts her bike in the garage."
      },
      {
        "type": "true_false",
        "prompt": "Lily rides her bike after the rain stops.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Lily decides to ride her bike tomorrow instead."
      },
      {
        "type": "choice",
        "prompt": "Why does Lily send Ellie a message?",
        "options": [
          "She needs a new recipe",
          "They cannot meet in the park",
          "Her bike is broken"
        ],
        "answer": 1,
        "evidence": "She sends Ellie a message to say that they cannot meet in the park."
      },
      {
        "type": "choice",
        "prompt": "What shape is the cookie for Lily's mother?",
        "options": [
          "A heart",
          "A square",
          "A star"
        ],
        "answer": 0,
        "evidence": "Lily makes one cookie in the shape of a heart for her mother."
      },
      {
        "type": "choice",
        "prompt": "What does Lily bring for the bike ride with Ellie?",
        "options": [
          "A bag of flour",
          "Two cookies",
          "A pack of cards"
        ],
        "answer": 1,
        "evidence": "They stop for a rest near a tree and eat two cookies that Lily has brought from home."
      },
      {
        "type": "true_false",
        "prompt": "Lily writes the recipe in her notebook.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "She writes the cookie recipe in her notebook so she can make them again."
      },
      {
        "type": "true_false",
        "prompt": "The girls ride quickly through the remaining puddles.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "The girls ride slowly along the path because some puddles are still there."
      }
    ]
  },
  {
    "id": "a1-04",
    "level": "A1",
    "title": "An email to a friend",
    "titleUk": "Лист до друга",
    "paragraphs": [
      "Hi Sam! I am writing from Odesa. My family and I are here for four days. Our hotel is near the sea. In the morning we swim, and in the afternoon we visit different places. Yesterday we went to a museum. Tomorrow we want to take a boat trip. I bought you a small gift at a shop near the hotel.",
      "We arrived on Tuesday afternoon by train. Dad wanted to take a taxi to the hotel, but the weather was nice, so we walked instead. It took us about twenty minutes. My little brother carried his own small bag. When we reached the hotel, the woman at the desk gave us a map of the town and told us about some places to visit.",
      "Our room has two large windows. From one of them I can see a street with trees and cafés. We leave the room early each morning because we do not want to miss the good weather. We take towels and a bottle of water to the beach. The sea is cool at first, but it feels lovely after a few minutes.",
      "Yesterday the museum was very interesting. We saw old photographs, maps and small models of ships. My brother liked a model of a large white ship. I liked the photographs of the city many years ago. I bought a postcard in the museum shop and wrote a few lines on the back. I want to show it to you when I come home.",
      "After the museum, we ate lunch in a café. I had a bowl of soup and some bread. Mum tried a dish with fish, and my brother ordered potatoes. We sat outside because there was a little wind and it was not too hot. Later, we walked through a park and found a place to sit in the shade.",
      "Today we went to a small shop that sells handmade things. I found a present for you there. I cannot tell you what it is yet because I want it to be a surprise. I also bought a notebook for myself. It has a picture of the sea on the cover, and I plan to use it in English class.",
      "Dad is checking the weather for tomorrow. If it is fine, we will go on the boat trip. We have not bought tickets yet because we want to see how windy it is in the morning. If the weather is bad, we will visit another museum instead. My brother hopes to see the city from the water.",
      "We will pack our bags on Thursday evening. I have to remember to put my wet towel in a separate bag. On Friday we will have breakfast and then go to the station. I hope the journey home is quiet because I want to finish my book on the train. Tell me what you have been doing this week. I look forward to seeing you and hearing all your news.",
      "There is one more place that I want to tell you about. Near the hotel there is a small bookshop. It has books in several languages, including English. I found a short story about a family that travels to different cities. It was not too difficult, so I bought it to read on the journey home. Mum said that I could choose one book as a holiday present. I have already read the first few pages, and I think you might like the story too.",
      "My brother has been writing about our holiday in a little diary. He draws pictures of the places we visit and writes a few words under each picture. Yesterday he drew the museum and a ship. Today he drew the beach, with a very large sun above the sea. I have taken some photographs, but I like his pictures because they show what he remembers most clearly. We want to make a page together when we get home, with one picture from each day. Perhaps we can show you the page when you visit us next week. I hope you are having a good week at home.",
      "See you on Friday! Love, Kate."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "How long is the family staying?",
        "options": [
          "Two days",
          "A week",
          "Four days"
        ],
        "answer": 2,
        "evidence": "My family and I are here for four days."
      },
      {
        "type": "choice",
        "prompt": "What did they do yesterday?",
        "options": [
          "Went home",
          "Visited a museum",
          "Took a boat trip"
        ],
        "answer": 1,
        "evidence": "Yesterday we went to a museum."
      },
      {
        "type": "choice",
        "prompt": "Who is the gift for?",
        "options": [
          "Sam",
          "Kate",
          "The hotel owner"
        ],
        "answer": 0,
        "evidence": "I bought you a small gift."
      },
      {
        "type": "true_false",
        "prompt": "They plan to take a train trip tomorrow.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Tomorrow we want to take a boat trip."
      },
      {
        "type": "true_false",
        "prompt": "The hotel is near the sea.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Our hotel is near the sea."
      },
      {
        "type": "choice",
        "prompt": "How does the family get from the station to the hotel?",
        "options": [
          "On foot",
          "By taxi",
          "By bus"
        ],
        "answer": 0,
        "evidence": "Dad wanted to take a taxi to the hotel, but the weather was nice, so we walked instead."
      },
      {
        "type": "choice",
        "prompt": "What does Kate buy for herself at the handmade shop?",
        "options": [
          "A model ship",
          "A bag",
          "A notebook"
        ],
        "answer": 2,
        "evidence": "I also bought a notebook for myself."
      },
      {
        "type": "choice",
        "prompt": "What does Kate's brother put in his diary?",
        "options": [
          "Only lists of prices",
          "Pictures and a few words",
          "Train timetables"
        ],
        "answer": 1,
        "evidence": "He draws pictures of the places we visit and writes a few words under each picture."
      },
      {
        "type": "true_false",
        "prompt": "Kate likes the old photographs at the museum.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "I liked the photographs of the city many years ago."
      },
      {
        "type": "true_false",
        "prompt": "Kate chooses a book in a language other than English because she cannot find English books.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "It has books in several languages, including English."
      }
    ]
  },
  {
    "id": "a1-05",
    "level": "A1",
    "title": "The lost keys",
    "titleUk": "Загублені ключі",
    "paragraphs": [
      "Paul comes home from work at five. He looks in his bag, but his keys are not there. He calls his sister, who is still at work. She tells him to look in the pocket of his coat. Paul checks the coat and finds the keys. He laughs because he always puts them in his bag. He opens the door and makes a cup of tea.",
      "It has been a long day at the office, and Paul wants to sit down for a few minutes. He has a bag with his lunch box, a book and some papers from work. He usually keeps his keys in a small pocket inside the bag. Today the pocket is empty. He takes everything out and puts it on a bench near his door.",
      "Paul looks under the bench and on the ground. He remembers using his keys in the morning when he left the house. He thinks he may have put them on his desk at work. His office is on the other side of town, so going back would take a long time. Before he does that, he decides to ask his sister for advice.",
      "His sister answers the phone during a short break. She asks him if he changed his coat that morning. Paul remembers that it was cold outside, so he put on an old brown coat instead of his usual jacket. His sister says that he sometimes uses the coat pocket when his hands are full. Paul checks the pockets.",
      "The keys are in the left pocket. They are under a small piece of paper with the name of a shop on it. Paul feels happy and a little silly. He thanks his sister and tells her that dinner will be ready when she comes home. Then he puts the papers and his lunch box back in his bag.",
      "Inside the house, Paul takes off his coat and hangs it by the door. He turns on the kettle and makes tea. While he waits, he looks around the kitchen for a good place to keep the keys. There is a small empty dish on a shelf near the entrance. He moves the dish to a place where it is easy to see.",
      "Later his sister arrives home. Paul shows her the dish and tells her his new plan. From now on, he wants to put his keys there every evening. In the morning he can take them when he puts on his shoes. His sister says that she uses a hook near the door for the same reason.",
      "The next day, Paul does not need to search his bag before leaving. He takes his keys from the dish and goes to work. When he returns that evening, he remembers to put them back. It is a small change, but it makes his mornings easier. He is glad that he did not have to travel all the way back to the office to find them.",
      "At the end of the week, Paul notices another small problem. He sometimes leaves his shopping list at home because it is on a piece of paper in the kitchen. On Saturday, he decides to keep a notebook next to his keys. When he remembers something he needs, he can write it down in the notebook. Before going to the shop, he can take the notebook with him. His sister tells him that she keeps a list on her phone instead. Paul likes using paper, so he chooses the method that is easier for him.",
      "They also make a plan for the things they share at home. There is a place for the spare key, and they agree not to move it without telling each other. Paul puts a hook near the door for his bag. His sister uses another hook for her coat. They do not need to make the house look perfect. They just want to find the things they use every day.",
      "A few days later, Paul leaves home early for a meeting. He has breakfast, picks up his bag and takes the keys from the dish. He arrives at work on time and feels less worried. He remembers how long he spent looking for the keys on Monday. It is funny that such a little thing caused such a big problem."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "When does Paul come home?",
        "options": [
          "At four",
          "At five",
          "At six"
        ],
        "answer": 1,
        "evidence": "Paul comes home from work at five."
      },
      {
        "type": "true_false",
        "prompt": "His sister is still at work.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "His sister, who is still at work."
      },
      {
        "type": "choice",
        "prompt": "Who helps Paul?",
        "options": [
          "His sister",
          "His neighbour",
          "His father"
        ],
        "answer": 0,
        "evidence": "He calls his sister."
      },
      {
        "type": "choice",
        "prompt": "Where are the keys?",
        "options": [
          "In his bag",
          "On the table",
          "In his coat pocket"
        ],
        "answer": 2,
        "evidence": "Paul checks the coat and finds the keys."
      },
      {
        "type": "true_false",
        "prompt": "Paul makes coffee after opening the door.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "He opens the door and makes a cup of tea."
      },
      {
        "type": "choice",
        "prompt": "Why did Paul wear a different coat that morning?",
        "options": [
          "His usual coat was lost",
          "His sister asked him to",
          "It was cold outside"
        ],
        "answer": 2,
        "evidence": "Paul remembers that it was cold outside, so he put on an old brown coat instead of his usual jacket."
      },
      {
        "type": "choice",
        "prompt": "Which pocket contains the keys?",
        "options": [
          "The right pocket",
          "The left pocket",
          "The bag pocket"
        ],
        "answer": 1,
        "evidence": "The keys are in the left pocket."
      },
      {
        "type": "choice",
        "prompt": "What does Paul put next to the keys at the end of the week?",
        "options": [
          "A notebook",
          "A telephone",
          "A coat"
        ],
        "answer": 0,
        "evidence": "On Saturday, he decides to keep a notebook next to his keys."
      },
      {
        "type": "true_false",
        "prompt": "Paul promises to prepare dinner before his sister gets home.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "He thanks his sister and tells her that dinner will be ready when she comes home."
      },
      {
        "type": "true_false",
        "prompt": "Paul chooses to use a shopping list on his phone instead of paper.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Paul likes using paper, so he chooses the method that is easier for him."
      }
    ]
  },
  {
    "id": "a1-06",
    "level": "A1",
    "title": "A visit to the library",
    "titleUk": "Візит до бібліотеки",
    "paragraphs": [
      "The library opens at ten on Saturdays. Ella arrives at eleven to return a book about animals. She wants to borrow a new story, but she cannot choose one. A librarian helps her find a book about a girl who travels by train. Ella sits by the window and reads the first page. She likes it and takes the book home. She must return it in two weeks.",
      "The library is on a quiet street next to a park. Near the entrance there is a desk where people return books. A sign tells visitors to speak quietly. There are shelves for stories, school books and books about travel. Near the window, there are a few comfortable chairs for people who want to read.",
      "The librarian explains that a library card is useful because it helps the library remember which books each person has taken home. She also shows where to find the date when a book must be returned. Readers can ask to keep a book for longer if nobody else is waiting for it. It is important to bring books back in good condition.",
      "In the children's section, there are books with pictures and longer stories with fewer pictures. It is not always easy to choose something to read. One good idea is to open a book and read the first page. If there are too many difficult words, a shorter book may be better. If the story sounds interesting, it is worth taking it home.",
      "There is also a table with new books. Some are about animals and some are about people who travel to different countries. A small card beside each book gives its title and a few words about the story. Readers can look at the cards before they make a choice. The librarian is happy to suggest a book when someone needs help.",
      "A few people are working on computers at the back of the library. Another person is reading a newspaper. Everyone has a different reason for being there. Some students come after school because their homes are busy and they need a quiet place to study. Other people simply enjoy reading in a comfortable chair.",
      "Before leaving, visitors check that they have their library cards and the right books. The librarian puts each book into the computer system and tells them the return date. They can put the date in a notebook or on a calendar at home. A library is a good place to try new kinds of stories without buying every book.",
      "When Ella gets home, she puts the new book on her desk. She wants to read a few pages every evening, but she does not want to leave all the reading until the last day. Her father helps her write the return date on the calendar in the kitchen. Ella begins reading after dinner. In the first chapter, the girl in the story buys a train ticket and meets an interesting person at the station. Ella is curious about what will happen next.",
      "The next Saturday, Ella visits the library again with her friend Grace. Grace usually reads books about sport and does not know where to find other kinds of stories. Ella shows her the table with new books and explains how she chose her own story. Grace reads the first page of a book about a young runner. She decides to borrow it. The girls sit by the window for a while and read quietly. They enjoy spending time together even though they are reading different books.",
      "Two weeks after her first visit, Ella finishes the story and returns it on time. She tells the librarian that she enjoyed reading about the train journey. The librarian suggests another book by the same writer. Ella looks at it and decides to borrow it. This time she chooses a second book too, because she has a few days off school. She feels pleased that she has discovered a new kind of story and wants to visit the library more often."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "When does Ella arrive?",
        "options": [
          "At eleven",
          "At ten",
          "At twelve"
        ],
        "answer": 0,
        "evidence": "Ella arrives at eleven."
      },
      {
        "type": "choice",
        "prompt": "What is the new book about?",
        "options": [
          "Animals in the sea",
          "A boy playing tennis",
          "A girl travelling by train"
        ],
        "answer": 2,
        "evidence": "A book about a girl who travels by train."
      },
      {
        "type": "choice",
        "prompt": "When must Ella return it?",
        "options": [
          "In a month",
          "In two weeks",
          "Tomorrow"
        ],
        "answer": 1,
        "evidence": "She must return it in two weeks."
      },
      {
        "type": "true_false",
        "prompt": "Ella buys the new book.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "She wants to borrow a new story."
      },
      {
        "type": "true_false",
        "prompt": "Ella reads the first page at the library.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Ella sits by the window and reads the first page."
      },
      {
        "type": "choice",
        "prompt": "What can readers do if nobody is waiting for their borrowed book?",
        "options": [
          "Keep it without telling the library",
          "Ask to keep it longer",
          "Give it away"
        ],
        "answer": 1,
        "evidence": "Readers can ask to keep a book for longer if nobody else is waiting for it."
      },
      {
        "type": "choice",
        "prompt": "What is one way to choose a suitable book?",
        "options": [
          "Read the first page",
          "Choose the heaviest book",
          "Count all the pictures"
        ],
        "answer": 0,
        "evidence": "One good idea is to open a book and read the first page."
      },
      {
        "type": "choice",
        "prompt": "Who goes to the library with Ella the next Saturday?",
        "options": [
          "Grace",
          "Her father",
          "The librarian"
        ],
        "answer": 0,
        "evidence": "The next Saturday, Ella visits the library again with her friend Grace."
      },
      {
        "type": "true_false",
        "prompt": "There is a table with new books.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "There is also a table with new books."
      },
      {
        "type": "true_false",
        "prompt": "Ella returns her first borrowed story late.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Two weeks after her first visit, Ella finishes the story and returns it on time."
      }
    ]
  },
  {
    "id": "a2-01",
    "level": "A2",
    "title": "A surprising birthday",
    "titleUk": "Несподіваний день народження",
    "paragraphs": [
      "Last Friday, Daniel thought everyone had forgotten his birthday. His classmates said nothing in the morning, and his parents left for work as usual. After school, his friend Olivia invited him to the café near their house. When he opened the door, ten friends shouted, “Happy birthday!” They had decorated a table with balloons and prepared his favourite chocolate cake. Olivia explained that they had planned the surprise for two weeks. Daniel felt silly for being worried, but he was also very grateful. He said it was the best birthday he had ever had.",
      "That morning Daniel had checked his phone as soon as he woke up. There were messages about a school project and a football game, but not a single birthday message from his closest friends. He did not want to remind anyone, so he got dressed and went downstairs. His parents were getting ready for work. His mother asked him to take an umbrella because rain was expected in the afternoon. His father told him not to be late for school. Everything seemed ordinary.",
      "At school Daniel found it difficult to concentrate. During the break, he almost told Olivia that he was upset, but she was talking to another classmate about homework. He decided that perhaps birthdays were not as important to other people as they were to him. At lunch he ate with his friends as usual. They were friendly, yet nobody mentioned the date. He wondered whether he had forgotten one of their birthdays in the past.",
      "Meanwhile, Olivia had been working on a secret plan. Two weeks earlier, she had asked Daniel's parents if they could help organise a celebration. His mother had ordered a cake from a bakery and his father had spoken to the café owner. Olivia had sent a message to the other friends and asked everyone to arrive before Daniel. One friend had offered to bring balloons, while another had made a card with photographs from their school trips. They had agreed not to send birthday messages until the party began.",
      "After lessons, Olivia told Daniel that she wanted to get something to drink before going home. Daniel agreed, although he did not really feel like going out. He noticed that Olivia kept checking the time, but he thought she had another appointment later. When they reached the café, the lights near the back table were off. Olivia opened the door and encouraged Daniel to go in first. Suddenly the lights came on and his friends stood up.",
      "For a few seconds Daniel did not know what to say. Then he began to laugh. His parents arrived a little later and explained why they had behaved so normally that morning. His mother had found it especially hard to keep the secret. Everyone took turns writing a short birthday wish on the card. Daniel read the messages aloud and thanked his friends for the time they had spent preparing the surprise. They cut the cake and shared it with one another.",
      "When Daniel got home, he put the card on a shelf in his room. He realised that he had judged his friends too quickly. They had not forgotten him; they had been doing something kind in secret. At the same time, he told Olivia the next day that the silence at school had made him feel sad. She understood and said that next time they might plan a surprise without making someone feel forgotten. Daniel agreed. A good surprise should bring happiness, not unnecessary worry.",
      "A month later, Daniel learned that another classmate, Max, was going to have a birthday. Some of the friends suggested organising another surprise. Daniel remembered how he had felt when everyone had appeared to forget his birthday. He suggested a slightly different plan. They could wish Max a happy birthday at school as usual and invite him to a small celebration in the afternoon without telling him every detail. The friends agreed that a surprise did not have to begin with an uncomfortable experience.",
      "They first asked Max's parents whether he would be free after school. His parents explained that the family already had plans for the evening, but Max would have time for a short visit to a café. The friends decided not to arrange anything that would interfere with the family celebration. Olivia made a simple list of things to prepare. One friend offered to bring a card, another offered to take a few photographs, and Daniel offered to choose a game that everyone could play at the table.",
      "They also discussed the cost. Not everyone had the same amount of money to spend, and Daniel did not want anyone to feel that they needed to buy an expensive present. They decided to share the price of a small cake and make the card themselves. Each person could write a message inside it. The café owner agreed that they could use a table for a short time if they ordered something to eat or drink. The plan was simple enough for them to organise without much trouble.",
      "When Max's birthday arrived, his friends congratulated him in the morning. He was pleased that they remembered. After school, they invited him to the café, where the card and cake were waiting. He was surprised, but he had not spent the whole day feeling worried. Daniel enjoyed seeing how well the new plan worked. He also noticed that the celebration was not less special simply because Max knew his friends had remembered his birthday. The unexpected part was the extra effort they had made.",
      "Later, Daniel and Olivia talked about the two celebrations. They agreed that people did not all enjoy the same kind of surprise. Some might love a large party, while others might prefer a quiet afternoon with a few friends. The best way to prepare a celebration was to think about what the person being celebrated would enjoy. Daniel kept both birthday cards in his memory box, one from his own party and a small photograph from Max's. The experiences helped him understand that good intentions and careful planning were both important when trying to make someone happy."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Why was Daniel worried?",
        "options": [
          "He had lost his present.",
          "He did not like the café.",
          "He thought people had forgotten his birthday."
        ],
        "answer": 2,
        "evidence": "Daniel thought everyone had forgotten his birthday."
      },
      {
        "type": "choice",
        "prompt": "Who invited him to the café?",
        "options": [
          "His teacher",
          "Olivia",
          "His parents"
        ],
        "answer": 1,
        "evidence": "His friend Olivia invited him to the café."
      },
      {
        "type": "choice",
        "prompt": "How long had they planned the surprise?",
        "options": [
          "Two weeks",
          "One day",
          "A month"
        ],
        "answer": 0,
        "evidence": "They had planned the surprise for two weeks."
      },
      {
        "type": "true_false",
        "prompt": "The cake was chocolate.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "His favourite chocolate cake."
      },
      {
        "type": "true_false",
        "prompt": "Daniel knew about the party before school.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "He thought everyone had forgotten his birthday."
      },
      {
        "type": "choice",
        "prompt": "Why did Daniel's mother tell him to take an umbrella?",
        "options": [
          "Rain was expected",
          "He was going to the beach",
          "His old umbrella was missing"
        ],
        "answer": 0,
        "evidence": "His mother asked him to take an umbrella because rain was expected in the afternoon."
      },
      {
        "type": "choice",
        "prompt": "Who ordered the cake?",
        "options": [
          "Daniel's father",
          "Olivia",
          "Daniel's mother"
        ],
        "answer": 2,
        "evidence": "His mother had ordered a cake from a bakery and his father had spoken to the café owner."
      },
      {
        "type": "choice",
        "prompt": "How do the friends change the plan for Max's birthday?",
        "options": [
          "They greet him in the morning and surprise him later",
          "They stop speaking to him for the whole day",
          "They organise a party during his family dinner"
        ],
        "answer": 0,
        "evidence": "They could wish Max a happy birthday at school as usual and invite him to a small celebration in the afternoon without telling him every detail."
      },
      {
        "type": "true_false",
        "prompt": "Daniel tells Olivia that the silence made him sad.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "At the same time, he told Olivia the next day that the silence at school had made him feel sad."
      },
      {
        "type": "true_false",
        "prompt": "The friends require each person to buy an expensive present for Max.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Not everyone had the same amount of money to spend, and Daniel did not want anyone to feel that they needed to buy an expensive present."
      }
    ]
  },
  {
    "id": "a2-02",
    "level": "A2",
    "title": "The school garden",
    "titleUk": "Шкільний сад",
    "paragraphs": [
      "At the beginning of spring, a group of students decided to turn an empty corner of the school yard into a garden. Their science teacher showed them how to prepare the soil. They planted tomatoes, carrots and flowers, then made a schedule for watering. At first, some plants did not grow well because the ground was too dry. The students collected rainwater in large containers and used it during hot days. By June, the garden was full of colour. The class gave some vegetables to the school kitchen and planned to continue the project next year.",
      "The corner of the yard had been used to store old sports equipment. In winter it was often muddy, and students rarely went there. When their teacher asked for ideas to improve the school, Maya suggested planting a few vegetables. She had helped her grandfather in his garden and wanted to share what she knew. Other students preferred flowers because they thought the yard looked rather grey. The class decided that there was room for both.",
      "Before buying seeds, the students measured the area and drew a simple plan. They noticed that one part received sunlight for most of the day, while the wall of the school provided shade in the other part. The teacher explained that different plants needed different amounts of light. Tomatoes would go in the sunny area. The students planned to leave a narrow path between the beds so that they could water the plants without stepping on them.",
      "They asked the school caretaker for permission to use some tools. He showed them where to find gloves and small spades. On the first Friday of the project, the students removed stones and pieces of rubbish. They worked in pairs and filled several buckets. The soil was hard, so they had to spend more time preparing it than they had expected. Afterwards they washed the tools and returned them to the cupboard.",
      "When the seeds began to grow, the students were excited. They checked the beds during breaks and wrote the dates in a garden notebook. However, a week of warm weather caused a problem. Some of the small plants looked weak. The students had been watering only on school days, and nobody had thought about weekends. They made a new schedule, with an adult helping on days when the school was closed.",
      "To avoid using too much water from the tap, they collected rainwater in covered containers. The teacher explained that the containers needed to be kept safe and clean. The students also put some dry leaves around the plants to help the ground stay wet for longer. They compared two parts of the garden and noticed that the soil under the leaves did not dry out as quickly.",
      "By June there were tomatoes on the plants and bright flowers beside the path. The class invited other students to visit. They made small signs with the names of the plants and described what they had learned. A few vegetables went to the school kitchen. The cook thanked them and used some of their tomatoes in a salad. At the end of the term, the students wrote a plan for next spring, including a longer watering schedule and a list of seeds. The garden had become a practical lesson in planning, science and teamwork.",
      "When the school opened again after the summer break, the students visited the garden to see what had happened while they were away. Some plants had finished producing vegetables, and others were still growing. The school caretaker had helped look after the garden during the holidays, but several beds needed attention. The class took photographs of each area and compared them with the pictures they had made in spring. They could see clearly which plants had grown well and which had needed more care.",
      "The teacher asked the students to prepare a short report rather than simply say that the project had been successful. They discussed which parts of their original plan had worked. The sunny bed had been a good place for the tomatoes, and the narrow paths had made it easier to reach the plants. However, some of the labels had become difficult to read after several months outside. They decided to make stronger labels next year and write the names of the plants in both Ukrainian and English. This would help students practise vocabulary while visiting the garden.",
      "Another group wanted to know how much the project had cost. They looked at the receipts from the shops and made a list of the seeds, tools and containers they had used. Many of the tools belonged to the school, so they had not needed to buy everything. They also noted which materials could be used again. Their teacher explained that keeping records would make it easier to plan the next garden and ask for money only when it was necessary.",
      "The students decided to invite a younger class to join them for one afternoon. They prepared simple tasks, such as identifying plants, drawing leaves and reading the labels. They made sure that an adult was nearby whenever someone used a tool. The younger students enjoyed the visit and asked many questions. Maya explained that she had learned about gardening from her grandfather, but she had also learned new things through the school project. Some of the younger students suggested plants they would like to grow in the future.",
      "At the final meeting, the class discussed whether the garden should become a permanent part of school life. They agreed that it would need a group of students and adults who could share responsibility for it throughout the year. They also wanted to make sure that the garden remained useful for lessons rather than becoming a forgotten corner of the yard again. They prepared a simple calendar with tasks for autumn, winter and spring. The project had started with a few seeds and an empty space, but it had grown into something that different classes could learn from. The students were especially proud that they had found solutions when their first plans had not worked."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What did the teacher help them do?",
        "options": [
          "Buy containers",
          "Prepare the soil",
          "Build a kitchen"
        ],
        "answer": 1,
        "evidence": "Their science teacher showed them how to prepare the soil."
      },
      {
        "type": "true_false",
        "prompt": "The students used only water from a tap.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "The students collected rainwater in large containers."
      },
      {
        "type": "choice",
        "prompt": "Why did some plants grow poorly?",
        "options": [
          "The ground was too dry.",
          "There was too much rain.",
          "The students planted them in winter."
        ],
        "answer": 0,
        "evidence": "Some plants did not grow well because the ground was too dry."
      },
      {
        "type": "choice",
        "prompt": "Where did some vegetables go?",
        "options": [
          "The market",
          "The science lab",
          "The school kitchen"
        ],
        "answer": 2,
        "evidence": "The class gave some vegetables to the school kitchen."
      },
      {
        "type": "true_false",
        "prompt": "The garden started in spring.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "At the beginning of spring."
      },
      {
        "type": "choice",
        "prompt": "What had the empty corner been used for?",
        "options": [
          "Growing flowers",
          "Parking bicycles",
          "Storing sports equipment"
        ],
        "answer": 2,
        "evidence": "The corner of the yard had been used to store old sports equipment."
      },
      {
        "type": "choice",
        "prompt": "Where did the class plan to plant tomatoes?",
        "options": [
          "In the shaded area",
          "In the sunny area",
          "On the path"
        ],
        "answer": 1,
        "evidence": "Tomatoes would go in the sunny area."
      },
      {
        "type": "choice",
        "prompt": "How will the students improve the garden labels next year?",
        "options": [
          "By writing names in Ukrainian and English",
          "By replacing every label with a photograph",
          "By removing all plant names"
        ],
        "answer": 0,
        "evidence": "They decided to make stronger labels next year and write the names of the plants in both Ukrainian and English."
      },
      {
        "type": "true_false",
        "prompt": "The students recorded dates in a garden notebook.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "They checked the beds during breaks and wrote the dates in a garden notebook."
      },
      {
        "type": "true_false",
        "prompt": "The students decide that the garden requires no care outside spring.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "They prepared a simple calendar with tasks for autumn, winter and spring."
      }
    ]
  },
  {
    "id": "a2-03",
    "level": "A2",
    "title": "A weekend without a phone",
    "titleUk": "Вихідні без телефону",
    "paragraphs": [
      "Emma spends a lot of time on her phone, especially when she is bored. One weekend, she decided to leave it at home while visiting her aunt in the countryside. On Saturday morning, she felt strange without messages or videos. Her aunt suggested walking to a nearby lake. They took sandwiches and watched birds by the water. In the evening, Emma helped cook dinner and read a book. By Sunday, she had stopped thinking about her phone so often. She did not want to give it up completely, but she decided to spend less time looking at the screen.",
      "Before leaving, Emma told her parents where she would be staying. Her aunt had a telephone at home, so Emma could contact her family if she needed to. Emma turned off her own phone and put it in a drawer. She packed clothes, a book and a notebook. On the way to her aunt's house, she found herself reaching for the pocket where she normally kept her phone. It took a while to get used to the idea that it was not there.",
      "On Saturday her aunt made breakfast and asked Emma to help choose what they would do. Emma usually looked at videos while eating, but this time she listened to the sounds outside. She could hear birds and a tractor in a nearby field. Her aunt showed her a map of the area and pointed to a lake that was a short walk away. They prepared food, filled water bottles and set off.",
      "At first Emma wanted to take photographs of everything. She thought it would be a shame not to have a picture of the lake. Her aunt suggested drawing the scene instead. Emma was not very good at drawing, but she took her notebook out of her bag and tried to show the trees and the water. She noticed a group of birds that she might not have seen if she had been looking at a screen. They ate their sandwiches on a bench and watched the birds for a while.",
      "In the afternoon they returned to the house. Emma helped her aunt prepare vegetables for dinner. While they worked, her aunt told her stories about the village and about Emma's mother when she was young. Emma asked questions and discovered several things she had never heard before. After dinner, she sat by the window and read the first three chapters of her book. She had brought it on several trips but had never got very far with it.",
      "On Sunday morning, Emma helped water the plants in the garden. Later they visited a neighbour who made beautiful wooden boxes. He explained how he chose the wood and showed Emma some of his finished work. She wrote the name of the village in her notebook so she could remember where she had met him. By then she had stopped wondering whether she had received new messages.",
      "When Emma returned home, there were several messages waiting for her. Most were not urgent. She replied to her friends and told them about the weekend. She did not decide that phones were bad; she still needed hers to organise schoolwork and keep in touch. Instead, she made a new plan. She would leave her phone outside her bedroom while reading and put it away during meals. She would also try to spend a little time outdoors every day. The weekend had shown her that being bored for a few minutes did not always need an immediate solution.",
      "During the first week back at school, Emma discovered that changing her habits at home was more difficult than leaving her phone behind for one weekend. Her homework often involved looking something up online, and her friends used messages to organise their plans. She did not want to miss important information. Instead of turning her phone off for the whole day, she decided to choose a few times when she would check messages. She told her close friends about this plan so that they would not expect an immediate reply every time.",
      "On Tuesday evening she began reading after dinner. At first she kept thinking about the messages she might be receiving. She put her phone in the living room and decided to read for twenty minutes. When the time was up, she realised that she wanted to finish the chapter. She continued reading for a little longer. Later she checked her messages and found that nothing urgent had happened. The experience gave her confidence that she could spend short periods away from the screen without causing problems.",
      "Emma also noticed that there were times when she used her phone for a useful purpose. On Thursday she had to practise English vocabulary. She used an online dictionary to check the meaning of a new word and listened to its pronunciation. She then wrote the word and an example in her notebook. She felt that this was different from spending a long time watching videos without deciding what to watch. The phone had helped her complete a task, and she could put it away when the task was finished.",
      "At the weekend, Emma invited her friend Julia to walk with her in the local park. Julia wanted to take some photographs, and Emma did not mind. They took a few pictures together and then put their phones in their bags. They talked about school, watched a dog playing with a ball and planned to visit a café afterwards. Emma realised that she did not have to avoid all photographs or messages to enjoy being outside. She just wanted to pay attention to what was happening around her.",
      "After a month, Emma looked back at the plan she had made after visiting her aunt. Some parts had become easy, while others still needed practice. She sometimes spent longer on her phone than she intended, especially when she was tired. Instead of deciding that she had failed, she tried to understand what had happened and choose a better activity next time. Her aunt's quiet weekend had not changed everything in her life, but it had given her a useful example of how to spend time differently. Emma now tried to use her phone when it served a purpose and give other activities enough space in her day."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Where did Emma spend the weekend?",
        "options": [
          "In the countryside",
          "At a hotel",
          "In the city centre"
        ],
        "answer": 0,
        "evidence": "Visiting her aunt in the countryside."
      },
      {
        "type": "choice",
        "prompt": "What did they do at the lake?",
        "options": [
          "Went fishing",
          "Bought a phone",
          "Watched birds"
        ],
        "answer": 2,
        "evidence": "They took sandwiches and watched birds by the water."
      },
      {
        "type": "choice",
        "prompt": "What did Emma decide?",
        "options": [
          "To stop using phones forever",
          "To spend less time on her phone",
          "To buy a new phone"
        ],
        "answer": 1,
        "evidence": "She decided to spend less time looking at the screen."
      },
      {
        "type": "true_false",
        "prompt": "Emma felt strange on Saturday morning.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "On Saturday morning, she felt strange without messages or videos."
      },
      {
        "type": "true_false",
        "prompt": "Emma used her phone to watch videos at the lake.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "She decided to leave it at home."
      },
      {
        "type": "choice",
        "prompt": "How could Emma contact her family if necessary?",
        "options": [
          "By sending a letter",
          "Using her aunt's telephone",
          "Using her own phone"
        ],
        "answer": 1,
        "evidence": "Her aunt had a telephone at home, so Emma could contact her family if she needed to."
      },
      {
        "type": "choice",
        "prompt": "What did Emma do instead of taking photographs at the lake?",
        "options": [
          "She drew the scene",
          "She bought a postcard",
          "She wrote a poem"
        ],
        "answer": 0,
        "evidence": "Her aunt suggested drawing the scene instead."
      },
      {
        "type": "choice",
        "prompt": "How does Emma use her phone for her English homework?",
        "options": [
          "To avoid writing new words",
          "To play unrelated videos",
          "To check meaning and pronunciation"
        ],
        "answer": 2,
        "evidence": "She used an online dictionary to check the meaning of a new word and listened to its pronunciation."
      },
      {
        "type": "true_false",
        "prompt": "Emma plans to put her phone away during meals.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "She would leave her phone outside her bedroom while reading and put it away during meals."
      },
      {
        "type": "true_false",
        "prompt": "Emma's new plan is to turn off her phone for the whole day.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Instead of turning her phone off for the whole day, she decided to choose a few times when she would check messages."
      }
    ]
  },
  {
    "id": "a2-04",
    "level": "A2",
    "title": "The wrong train",
    "titleUk": "Не той потяг",
    "paragraphs": [
      "Alex was travelling to visit his cousin in another town. He arrived at the station early and bought a ticket. When a train stopped at platform four, he got on without checking the destination. After twenty minutes, he noticed that the names of the stations were unfamiliar. He asked the conductor for help and learned that he was going in the opposite direction. At the next station, he got off and found a train back. He arrived two hours late, but his cousin was waiting for him. Now Alex always checks the destination before getting on a train.",
      "Alex had never travelled to his cousin's town alone before. He had studied the timetable the evening before and saved the name of the station in a notebook. His cousin had sent him directions from the station to her house. Alex packed a small bag with clothes, a bottle of water and a book. He was proud that he could organise the trip without asking his parents to do everything for him.",
      "At the station he found the ticket office and bought a ticket. The woman at the desk told him that his train was due to leave from platform four. Alex looked at the large clock and saw that he still had time. He bought a sandwich and waited on a bench. There were several people standing nearby with bags. When a train arrived at the platform, he assumed that it was the one he needed. He followed some passengers into a carriage without looking at the information on the side of the train.",
      "He found a seat by the window and opened his book. The train left the station, and for the first few minutes everything seemed normal. At the next stop, Alex looked up and saw a station name he did not remember from the timetable. He checked his notebook, but the name was not there. When the train stopped again, he became more worried. He decided that the best thing to do was ask someone who worked on the train rather than guess.",
      "The conductor listened carefully and explained that another train used the same platform earlier in the day. Alex had boarded that train. The conductor told him the name of the next station and showed him where he could find information about trains going back. Alex thanked him and got off at the next stop. He stayed in the station and asked at the information desk for help with his return journey.",
      "While waiting, Alex sent a message to his cousin to explain what had happened. She replied that there was no need to hurry and asked him to tell her when he was on the correct train. Alex bought the appropriate ticket and checked the departure board twice. This time he also checked the destination displayed on the train itself. When he was sure it was correct, he got on and found a seat.",
      "His cousin met him at the station when he finally arrived. They walked home and had a late lunch together. Alex told her the whole story, including how he had asked the conductor for help. She said that many travellers make mistakes when they are in a hurry. Before his next journey, Alex decided to write down the departure time, the train number and the final destination. A platform number was useful, but it was not enough on its own. He felt more confident because he now knew what to check and what to do if something went wrong.",
      "The following month, Alex needed to make another journey by train. This time he prepared a little differently. He checked the timetable on the evening before the trip and wrote the station name, departure time and train number on one page of his notebook. He also checked whether there would be any changes along the route. His parents reminded him that the platform could change on the day of the journey, so it was important to look at the station information rather than depend only on the details he had written down at home.",
      "When Alex arrived at the station, he looked at the departure board before going to the platform. His train was still due to leave at the expected time. However, the board showed that it would leave from a different platform. An announcement confirmed the change. Alex went to the correct platform, checked the train number displayed near the entrance and compared it with his notebook. He noticed that another train was listed for a few minutes earlier. He waited until the correct train arrived before getting on.",
      "While travelling, Alex decided to keep track of the stations rather than read his book for the whole journey. He looked at the route map inside the carriage and checked the name of each major station. This helped him understand where he was and how much of the journey remained. He did not need to watch every moment, but he set a reminder to check the next stop shortly before he was due to arrive. When he reached his destination, he felt pleased that the journey had gone smoothly.",
      "His cousin asked him whether he was still worried about getting lost. Alex said that he felt more prepared than before. The first mistake had taught him that there were several pieces of information to check. He also knew that asking for help was an option if he became confused. He had saved the telephone numbers of his family and kept enough money for ordinary travel expenses. He understood that making plans in advance did not mean everything would always happen as expected, but it made it easier to deal with small changes.",
      "Later, a friend told Alex that he was going to travel alone for the first time. Alex explained what had happened on his previous trip and showed him the notes he now made before leaving. He did not tell his friend to worry about every possible problem. Instead, he suggested a few simple habits: check the destination, confirm the departure time, pay attention to announcements and ask an employee if something is unclear. His friend found the advice useful. Alex realised that a mistake could make him a better traveller if he learned from it instead of trying to forget about it."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What mistake did Alex make?",
        "options": [
          "He forgot to buy a ticket.",
          "He arrived after the train left.",
          "He boarded without checking the destination."
        ],
        "answer": 2,
        "evidence": "He got on without checking the destination."
      },
      {
        "type": "choice",
        "prompt": "Who helped him?",
        "options": [
          "A ticket seller",
          "The conductor",
          "His cousin"
        ],
        "answer": 1,
        "evidence": "He asked the conductor for help."
      },
      {
        "type": "choice",
        "prompt": "How late was he?",
        "options": [
          "Two hours",
          "Twenty minutes",
          "One hour"
        ],
        "answer": 0,
        "evidence": "He arrived two hours late."
      },
      {
        "type": "true_false",
        "prompt": "Alex stayed on the wrong train until the final station.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "At the next station, he got off."
      },
      {
        "type": "true_false",
        "prompt": "Alex bought a ticket before boarding.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "He arrived at the station early and bought a ticket."
      },
      {
        "type": "choice",
        "prompt": "What did Alex write in his notebook before leaving?",
        "options": [
          "The station name",
          "The conductor's name",
          "The price of lunch"
        ],
        "answer": 0,
        "evidence": "He had studied the timetable the evening before and saved the name of the station in a notebook."
      },
      {
        "type": "choice",
        "prompt": "Why did Alex board the wrong train?",
        "options": [
          "The station staff told him to board it",
          "He had the wrong ticket time printed on a sign",
          "Two trains used the same platform at different times"
        ],
        "answer": 2,
        "evidence": "The conductor listened carefully and explained that another train used the same platform earlier in the day."
      },
      {
        "type": "choice",
        "prompt": "What changes at the station on Alex's second trip?",
        "options": [
          "The name of his cousin",
          "The departure platform",
          "The destination of his journey"
        ],
        "answer": 1,
        "evidence": "However, the board showed that it would leave from a different platform."
      },
      {
        "type": "true_false",
        "prompt": "Alex informed his cousin about the mistake while waiting.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "While waiting, Alex sent a message to his cousin to explain what had happened."
      },
      {
        "type": "true_false",
        "prompt": "Alex boards the earlier train again without checking its number.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "He waited until the correct train arrived before getting on."
      }
    ]
  },
  {
    "id": "a2-05",
    "level": "A2",
    "title": "Learning to cook",
    "titleUk": "Вчуся готувати",
    "paragraphs": [
      "Sofia wanted to learn how to cook because her parents often worked late. She began with simple meals, such as pasta and vegetable soup. Her first soup was too salty, so she asked her grandmother for advice. Her grandmother told her to add salt slowly and taste the food while cooking. After a few weeks, Sofia could prepare dinner without help. She also learned to make a shopping list, which saved money and reduced waste. On Sunday, she cooked a meal for her whole family. Everyone enjoyed it, and her younger brother offered to wash the dishes.",
      "At first Sofia did not know where to begin. She had watched her parents cook many times, but she had never prepared a complete meal by herself. Her grandmother suggested choosing two simple recipes and practising them until she felt comfortable. Sofia wrote the ingredients in a notebook. She also asked her parents which kitchen tools she could use safely and which tasks needed an adult nearby.",
      "Her first plan was to make pasta with tomato sauce. She checked the cupboards before going to the shop and discovered that there was already a packet of pasta at home. She bought tomatoes and an onion instead. She followed the instructions on the pasta packet and asked her mother to help with the hot pan. The meal was simple, but it was ready at the right time. Sofia was pleased that her family could eat something she had helped prepare.",
      "The next week she tried vegetable soup. She cut up vegetables, measured the water and added salt without thinking about the amount. When she tasted the soup, she knew something was wrong. It was much too salty. Her grandmother explained that it was easier to add more salt later than to remove salt that was already in the food. They discussed what had gone wrong, and Sofia wrote the advice next to the recipe.",
      "Sofia began to plan meals on Friday evenings. She checked what was left in the fridge and decided which ingredients could be used again. If there were carrots left from the soup, she could use them in a salad the next day. This helped her avoid buying more than the family needed. At the shop she compared prices and tried to choose vegetables that were in season. She learned that a shopping list was useful only if she had first checked what was already at home.",
      "As she gained confidence, she started to organise her time better. She prepared ingredients before she began cooking and cleaned the table as she worked. She kept raw food separate from ready-to-eat food and remembered to wash her hands. Her parents explained why these habits mattered. They were happy for her to do more, as long as she followed the safety rules they had agreed on.",
      "On Sunday she planned a complete meal for the family. Her father helped carry the shopping home, and her mother stayed nearby in the kitchen. Sofia made soup and a simple main dish. She set the table while the food was cooking and called everyone when it was ready. Her little brother said he wanted to learn to cook too. He offered to wash the dishes and asked Sofia to teach him how to make a sandwich. Sofia realised that learning to cook was not just about following recipes. It was also a way to share responsibility and spend time together.",
      "The next month Sofia decided that she wanted to prepare a different meal for a small family gathering. She chose a recipe that she had never tried before, but she did not wait until the day of the gathering to practise. She asked her grandmother to look through the recipe with her and help her decide whether she had the right equipment. They noticed that the original recipe was intended for four people, while eight people would be at the table. Sofia wrote down the quantities she would need and checked them carefully before making the shopping list.",
      "At the shop, she found that one of the vegetables in the recipe was not available. She called her grandmother and explained the problem. Her grandmother suggested choosing another vegetable that could be prepared in a similar way. Sofia compared the prices and chose one that looked fresh. She was pleased that she did not have to change the whole meal because one ingredient was missing. However, she also understood that some substitutions could change the result of a recipe, so it was sensible to ask when she was unsure.",
      "On the day of the gathering, Sofia began earlier than usual. She placed the ingredients in separate bowls and checked the order of the tasks. Her mother helped with the oven, and her younger brother set out the plates and glasses. One part of the meal was ready before the others, so Sofia asked her mother how to keep it safely until everyone was ready to eat. They avoided leaving food in unsuitable conditions and made sure everything was cooked and stored correctly. Sofia learned that timing was important when preparing several dishes at once.",
      "After dinner, the family helped clear the table. Sofia put the remaining food into suitable containers and wrote the date on them. Her parents explained which leftovers they could use the following day. The meal had cost less than they had expected because Sofia had used some ingredients that were already at home. She felt proud, not only because the food tasted good but also because everyone had worked together and there was little waste.",
      "A few days later she wrote the recipe in her notebook, including the changes she had made and the things she would do differently next time. She added a separate page with the meals she already knew how to prepare. Her goal was not to become an expert immediately. She wanted to learn a few reliable meals that were useful for everyday life. She also hoped to teach her brother some simple kitchen tasks when their parents were nearby. The cooking project had become a way for the whole family to share work, learn from one another and enjoy their time together."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Why did Sofia want to cook?",
        "options": [
          "She disliked all vegetables.",
          "Her parents often worked late.",
          "She wanted to open a restaurant."
        ],
        "answer": 1,
        "evidence": "Her parents often worked late."
      },
      {
        "type": "true_false",
        "prompt": "Her grandmother advised adding salt slowly.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Her grandmother told her to add salt slowly."
      },
      {
        "type": "choice",
        "prompt": "What was wrong with her first soup?",
        "options": [
          "It was too salty.",
          "It was too cold.",
          "It was too sweet."
        ],
        "answer": 0,
        "evidence": "Her first soup was too salty."
      },
      {
        "type": "choice",
        "prompt": "What helped her save money?",
        "options": [
          "Buying ready meals",
          "Eating out",
          "Making a shopping list"
        ],
        "answer": 2,
        "evidence": "She also learned to make a shopping list, which saved money."
      },
      {
        "type": "true_false",
        "prompt": "Her younger brother cooked the Sunday meal.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "On Sunday, she cooked a meal for her whole family."
      },
      {
        "type": "choice",
        "prompt": "What did Sofia already have when planning her first pasta meal?",
        "options": [
          "Tomatoes",
          "An onion",
          "A packet of pasta"
        ],
        "answer": 2,
        "evidence": "She checked the cupboards before going to the shop and discovered that there was already a packet of pasta at home."
      },
      {
        "type": "choice",
        "prompt": "When did Sofia start planning meals?",
        "options": [
          "Monday mornings",
          "Friday evenings",
          "Sunday afternoons"
        ],
        "answer": 1,
        "evidence": "Sofia began to plan meals on Friday evenings."
      },
      {
        "type": "choice",
        "prompt": "Why does Sofia change the quantities in a recipe for the family gathering?",
        "options": [
          "She has decided to skip the meal",
          "Her brother wants fewer dishes",
          "The original recipe served four, but eight people are coming"
        ],
        "answer": 2,
        "evidence": "They noticed that the original recipe was intended for four people, while eight people would be at the table."
      },
      {
        "type": "true_false",
        "prompt": "Sofia asked her parents which kitchen tasks needed an adult nearby.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "She also asked her parents which kitchen tools she could use safely and which tasks needed an adult nearby."
      },
      {
        "type": "true_false",
        "prompt": "Sofia throws away all remaining food after the gathering.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Sofia put the remaining food into suitable containers and wrote the date on them."
      }
    ]
  },
  {
    "id": "a2-06",
    "level": "A2",
    "title": "The football match",
    "titleUk": "Футбольний матч",
    "paragraphs": [
      "Our school football team played against a team from a nearby village last month. We were nervous because they had won their previous three matches. During the first half, our opponents scored twice. Our coach told us to stay calm and pass the ball more often instead of running alone. In the second half, we scored two goals, but neither team managed to score again. The match ended in a draw. Although we had not won, our coach was proud of the way we had worked together. We learned that good teamwork can be more important than individual skill.",
      "During the week before the match, our team trained after school. We knew the other team was strong because we had seen them play before. Their players moved quickly and passed the ball well. Our coach told us not to worry too much about their results. He wanted us to concentrate on our own game. We practised passing, moving into empty spaces and helping each other when someone lost the ball.",
      "On the morning of the match, we arrived early at the sports field. The grass was wet from rain the previous evening. We put on our football boots and warmed up together. Some parents and students came to watch. I felt nervous when I saw the other team arrive, but our captain reminded us that we had prepared well. We shook hands with the players before the referee started the game.",
      "In the first half, we tried to move forward too quickly. Several players ran with the ball instead of looking for a teammate. Our opponents noticed this and took the ball from us. They scored their first goal after a quick pass. A few minutes later, they scored again. We were disappointed and began to make even more mistakes. When the referee stopped the game for half-time, we walked back to the side of the field feeling tired.",
      "Our coach gave us water and asked us to listen. He did not shout at anyone. Instead, he drew a simple picture of the field and showed us where we could make more space. He asked our defenders to look up before passing and reminded the other players to offer help. Our captain said that we still had enough time to change the result if we played together.",
      "In the second half, we followed the plan more carefully. We made shorter passes and called to each other when we were free. Our first goal came after several players worked together near the other team's goal. Everyone became more confident. Later, one of our defenders passed to a player in the middle, who passed to our striker. The striker scored our second goal. We wanted to win, but we also knew that the other team could score again if we stopped paying attention.",
      "The last few minutes were difficult because both teams were tired. Our goalkeeper made an important save, and their goalkeeper stopped one of our shots. When the final whistle sounded, the score was equal. We thanked the referee and shook hands with the other team again. Our coach said that the second half had been our best performance that month. At the next training session we discussed what we had learned. We wanted to keep practising teamwork, not only shooting and running. A draw had taught us something that a lucky win might not have taught us.",
      "At the next training session, our coach asked us to describe one moment from the match when we had made a good decision. Some players talked about the goals, but others mentioned times when they had passed the ball instead of trying to score alone. Our goalkeeper said that he had felt more confident in the second half because the defenders had communicated with him. The coach wrote several of these ideas on a board and explained that important contributions were not always the ones that appeared on the scoreboard.",
      "We then divided into small groups and practised a passing exercise. The aim was to move the ball across a marked area without keeping it for too long. At first we made several mistakes because we were not looking at the positions of our teammates. When we slowed down and began calling to one another, the exercise became easier. We changed positions so that each player could experience the problems faced by other members of the team. I usually played further forward, but I learned that defenders often had to make quick decisions while looking at several players at the same time.",
      "Our captain suggested that we choose one practical goal for our next match. Instead of saying that we simply wanted to win, we decided to concentrate on moving into useful positions when a teammate had the ball. We could observe whether we were doing this even if the other team scored. Our coach liked the idea because it gave us something we could control. We knew that our opponents might be faster or more experienced, but we could still improve the way we worked together.",
      "A few weeks later we played another match. We made some good passes early in the game, and one of our players scored. The opposing team equalised before half-time. In the second half, we continued trying to communicate rather than become impatient. The final result was not the only thing we discussed afterwards. We also talked about how often we had helped a teammate who was under pressure. Our coach pointed out that we still needed practice, but our decisions were becoming more consistent.",
      "The experience changed how I thought about football. I still enjoyed scoring goals, and I wanted our team to win. However, I began to notice how many small actions made a goal possible. A player might move away from an opponent to create space, another might make a simple pass, and someone else might stop the other team from attacking. These actions did not always receive attention from the people watching the match. They were still important. I learned that individual improvement and teamwork could support each other. By helping the team play better, I was also becoming a more useful and confident player."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "How many goals did the other team score in the first half?",
        "options": [
          "Two",
          "One",
          "Three"
        ],
        "answer": 0,
        "evidence": "During the first half, our opponents scored twice."
      },
      {
        "type": "choice",
        "prompt": "What did the coach suggest?",
        "options": [
          "Running alone more often",
          "Changing the goalkeeper",
          "Passing the ball more often"
        ],
        "answer": 2,
        "evidence": "Pass the ball more often instead of running alone."
      },
      {
        "type": "choice",
        "prompt": "What was the final result?",
        "options": [
          "A victory for the village",
          "A draw",
          "A victory for our school"
        ],
        "answer": 1,
        "evidence": "The match ended in a draw."
      },
      {
        "type": "true_false",
        "prompt": "The coach was disappointed with their teamwork.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Our coach was proud of the way we had worked together."
      },
      {
        "type": "true_false",
        "prompt": "The opponents had won their previous three matches.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "They had won their previous three matches."
      },
      {
        "type": "choice",
        "prompt": "What was the grass like before the match?",
        "options": [
          "Very dry",
          "Wet",
          "Frozen"
        ],
        "answer": 1,
        "evidence": "The grass was wet from rain the previous evening."
      },
      {
        "type": "choice",
        "prompt": "How did the coach explain his plan at half-time?",
        "options": [
          "He drew a picture of the field",
          "He read a list of scores",
          "He showed a video"
        ],
        "answer": 0,
        "evidence": "Instead, he drew a simple picture of the field and showed us where we could make more space."
      },
      {
        "type": "choice",
        "prompt": "What practical goal does the team choose for its next match?",
        "options": [
          "To score only from long distances",
          "To avoid passing altogether",
          "To move into useful positions when a teammate has the ball"
        ],
        "answer": 2,
        "evidence": "Instead of saying that we simply wanted to win, we decided to concentrate on moving into useful positions when a teammate had the ball."
      },
      {
        "type": "true_false",
        "prompt": "The team made shorter passes in the second half.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "We made shorter passes and called to each other when we were free."
      },
      {
        "type": "true_false",
        "prompt": "The coach believes only actions on the scoreboard are important.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "The coach wrote several of these ideas on a board and explained that important contributions were not always the ones that appeared on the scoreboard."
      }
    ]
  },
  {
    "id": "b1-01",
    "level": "B1",
    "title": "Repair instead of replace",
    "titleUk": "Ремонтувати замість замінювати",
    "paragraphs": [
      "When a toaster broke in Marta’s flat, she assumed she would have to buy a new one. A neighbour recommended a monthly repair café, where volunteers help people fix everyday objects. Marta brought the toaster along, expecting someone to repair it while she waited. Instead, a volunteer explained the problem and showed her how to use basic tools safely while he supervised. The toaster worked again before lunch.",
      "Marta was surprised by how much she enjoyed the experience. She realised that replacing an object was often easier than investigating what was wrong with it, but not necessarily cheaper. The repair café also offered a chance to meet people who lived nearby. Not every object could be repaired, of course, and some electrical faults required professional attention. Nevertheless, Marta decided to visit again with a broken table lamp. She now checks whether something can be fixed before throwing it away.",
      "Before visiting the café, Marta had looked at several new toasters online. The cheapest models seemed affordable, but she remembered that the old one had lasted for years. Apart from the fault, it was in good condition. She also realised that she did not know what happened to small electrical appliances after they were thrown away. Her neighbour explained that the volunteers could help her understand whether the appliance was worth repairing, rather than promising that they could fix everything.",
      "The café took place in a community hall. At the entrance, visitors filled in a short form describing the problem with their objects. Some had brought clothes with torn pockets, others had broken bicycles or clocks. A volunteer directed each visitor to someone with relevant experience. Marta was asked not to connect her toaster to the electricity supply. The person helping her explained that electrical appliances needed special care and that only suitable, qualified volunteers should work on electrical faults.",
      "While she waited, she watched a woman learning to sew a button back onto a coat. The woman had expected to leave the coat and collect it later, but the volunteer encouraged her to try the repair herself. At another table, a bicycle owner was learning how to check the condition of a tyre. Marta began to understand that the event was intended to teach practical skills as well as restore objects. The atmosphere was relaxed, and people often shared advice about problems that had nothing to do with the items they had brought.",
      "After her toaster had been checked and safely repaired, Marta asked how much she owed. The café did not charge a fixed fee, although visitors could make a donation to help cover the cost of the room and materials. She gave what she could and stayed for a cup of tea. A retired carpenter told her that he enjoyed passing on skills that he had learned at work. A younger volunteer explained that she had started coming to the café because she wanted to learn from other people.",
      "At home, Marta made a list of objects that she had planned to replace. She noticed that a pair of trousers needed a small repair and a drawer handle was loose. She could deal with these simple problems herself after getting advice. Other items, however, were not appropriate for a home repair. She learned to distinguish an ordinary maintenance task from work requiring specialist equipment or training. She also considered the cost of replacement parts and the expected remaining life of the object.",
      "The experience changed her attitude towards buying things. Instead of choosing only on price, she began asking whether an item was likely to last and whether spare parts were available. She did not expect to repair every possession forever. Sometimes replacement was the sensible option, especially when safety or reliability could not be guaranteed. Nevertheless, taking a moment to consider repair helped her make decisions for better reasons than simply wanting something new. It also made her feel more connected to the people in her neighbourhood.",
      "At her next visit, Marta brought the table lamp that she had mentioned to the volunteers. She had not attempted to open it at home, because she was uncertain about the cause of the problem. At the café, the volunteer who had helped her before was working with someone else. Another volunteer listened to her description of the fault and explained which checks would be appropriate. While a professional examined the electrical parts, Marta looked through a collection of instruction sheets about ordinary household maintenance. She was interested in the difference between keeping an object in good condition and repairing something that had already stopped working.",
      "One instruction sheet described how furniture could become unstable when its connections gradually became loose. It suggested checking simple, accessible parts before the problem became serious. Marta remembered the drawer handle she had fixed at home. Another sheet explained how to care for clothes so that they lasted longer. She had previously thought of these activities as separate tasks, but she now saw that they shared a common purpose. Regular attention could sometimes prevent small faults from becoming larger problems. At the same time, the advice emphasised that people should ask for appropriate help when they were unsure whether an object was safe to use.",
      "The lamp turned out to need a part that the café did not have available. Marta had hoped to take it home in working condition that afternoon, but the volunteer explained that replacing the part without checking its suitability would be a bad idea. They wrote down the relevant information and discussed where she could obtain a suitable replacement. Marta decided to keep the lamp out of use until it had been dealt with properly. Although she left without a working lamp, she did not feel that the visit had been wasted. She understood more about the problem and had a realistic plan for dealing with it.",
      "During the following month, Marta noticed several examples of the different attitudes people had towards damaged possessions. A colleague complained that a bag was no longer useful because its zip had broken. When Marta suggested taking it to the repair café, the colleague said that she had never learned to sew and would probably make the problem worse. Marta explained that the volunteers did not expect visitors to arrive with practical experience. The colleague decided to attend the next event and discovered that replacing a zip required more skill than a simple button repair, but that a local tailor could do the work for a reasonable price.",
      "Marta began to understand that the decision to repair something was influenced by more than the condition of the object. Access to spare parts, the cost of professional work and the amount of time available all mattered. A person who worked long hours might find it difficult to attend a monthly event, while someone who lived far away might spend more on transport than on the repair itself. A cheaper replacement could be the only realistic choice for a household with very limited money. Telling everyone that they should repair their possessions would ignore these practical differences. The café was valuable because it offered another option, not because it made every other decision wrong.",
      "The organisers also had practical concerns of their own. They needed a room with suitable facilities, volunteers with a range of skills and a way to manage the number of visitors. On busy mornings, some people had to wait for a long time. The organisers tried using a simple appointment system for tasks that were likely to require more attention. They kept a few places available for people who arrived without booking, because not everyone knew how to describe a fault in advance. Volunteers were encouraged to explain clearly when a job was beyond their experience instead of attempting it simply because someone had brought the object to them.",
      "Marta offered to help with the reception desk. She did not consider herself a repair expert, but she was comfortable talking to visitors and writing down information about their objects. Her task was to ask a few basic questions, find the appropriate volunteer and explain that the café could not promise a successful repair. She also helped record whether objects had been repaired, required a specialist or could not reasonably be restored. These records gave the organisers a better idea of which skills and materials would be useful at future events. Marta enjoyed contributing in a way that matched her own abilities.",
      "After several months, she looked back at the first day when she had taken her toaster to the café. The most important change had not been the amount of money she had saved, although that was useful. She had become more confident about asking questions, more aware of the value of practical skills and more interested in the experiences of people around her. She still bought new things when they were needed. Before doing so, she considered whether the purchase would solve a real problem and whether the object was likely to remain useful for a long time. Repair had become one part of a more thoughtful approach to owning and using things."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What surprised Marta about the volunteer’s approach?",
        "options": [
          "He repaired it without speaking to her.",
          "He told her to buy a new toaster.",
          "He helped her learn to repair the toaster herself."
        ],
        "answer": 2,
        "evidence": "The volunteer explained the problem and showed her how to use basic tools safely while he supervised."
      },
      {
        "type": "choice",
        "prompt": "What additional benefit did she discover?",
        "options": [
          "Learning to sell old furniture",
          "Meeting people in her neighbourhood",
          "Getting free new appliances"
        ],
        "answer": 1,
        "evidence": "The repair café also offered a chance to meet people who lived nearby."
      },
      {
        "type": "choice",
        "prompt": "What is the main message?",
        "options": [
          "Consider repair before replacement.",
          "Every broken item can be repaired at home.",
          "New appliances are always cheaper."
        ],
        "answer": 0,
        "evidence": "She now checks whether something can be fixed before throwing it away."
      },
      {
        "type": "true_false",
        "prompt": "Some electrical faults need professional attention.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Some electrical faults required professional attention."
      },
      {
        "type": "true_false",
        "prompt": "The repair café meets every week.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "A neighbour recommended a monthly repair café."
      },
      {
        "type": "choice",
        "prompt": "What did visitors do at the entrance to the repair café?",
        "options": [
          "Describe the fault on a form",
          "Pay a fixed fee",
          "Choose new appliances"
        ],
        "answer": 0,
        "evidence": "At the entrance, visitors filled in a short form describing the problem with their objects."
      },
      {
        "type": "choice",
        "prompt": "How was the repair café funded in the example?",
        "options": [
          "A charge for every tool",
          "A compulsory repair fee",
          "Optional donations"
        ],
        "answer": 2,
        "evidence": "The café did not charge a fixed fee, although visitors could make a donation to help cover the cost of the room and materials."
      },
      {
        "type": "choice",
        "prompt": "What happens when Marta brings the lamp to the café?",
        "options": [
          "It needs a part that is not available",
          "It is repaired without checking the parts",
          "She immediately buys a new lamp"
        ],
        "answer": 0,
        "evidence": "The lamp turned out to need a part that the café did not have available."
      },
      {
        "type": "true_false",
        "prompt": "The café aimed to teach visitors practical skills.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Marta began to understand that the event was intended to teach practical skills as well as restore objects."
      },
      {
        "type": "true_false",
        "prompt": "Marta must become a repair specialist to contribute to the café.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "She did not consider herself a repair expert, but she was comfortable talking to visitors and writing down information about their objects."
      }
    ]
  },
  {
    "id": "b1-02",
    "level": "B1",
    "title": "A different kind of holiday",
    "titleUk": "Інший вид відпочинку",
    "paragraphs": [
      "For years, Oliver spent his holidays in busy cities, visiting famous buildings and eating in restaurants. Last summer, however, he joined a week-long conservation project in a forest. Volunteers cleared walking paths, recorded information about wildlife and collected litter. The work was tiring, particularly on the first few days, because Oliver was not used to getting up early.",
      "The group came from several countries, so they communicated in English even though most were not native speakers. In the evenings they cooked together and shared stories. Oliver found that his confidence in speaking English improved because he needed to use it for real tasks rather than classroom exercises. He also appreciated the slower pace of life. When he returned home, he felt more rested than after some of his city breaks, despite the physical work. He is considering another volunteer holiday next year, though he still enjoys visiting cities.",
      "Oliver first heard about the conservation project from a colleague who had spent a holiday helping to restore footpaths. The idea appealed to him, although he was uncertain about spending a week with strangers. He read the information provided by the organisers, checked what equipment he needed and asked about the daily routine. The project offered basic accommodation and training for beginners. It did not promise close encounters with wildlife or a completely comfortable stay. Volunteers were expected to cooperate and follow the instructions of experienced staff.",
      "On the first evening, the group met in a small building near the forest. Everyone introduced themselves and explained why they had joined. Some were interested in nature, some wanted to improve their practical skills, and others simply wanted a break from their usual routine. Oliver noticed that people spoke English with different accents. At first he worried that he might misunderstand someone, but he soon discovered that asking a person to repeat something was a normal part of the conversation.",
      "The following morning, a member of staff explained how to use the tools provided for maintaining the paths. The volunteers worked in small teams, with a leader who knew the area. They collected rubbish and removed small branches from marked routes. They were told to leave unfamiliar plants and animals alone and report anything unusual rather than try to deal with it themselves. At the end of each morning, the group recorded which section of the path had been checked. The records helped the organisers decide where more work was needed.",
      "Oliver found the early starts challenging. He had expected to spend most of his holiday outside, but he had not realised how tired he would feel after a full morning of physical activity. During the afternoon breaks he learned to slow down and drink enough water. He also began to appreciate the simple pleasure of sitting outdoors without trying to plan the next tourist attraction. The other volunteers had different levels of experience, and they learned to divide the tasks according to what each person could comfortably do.",
      "In the evenings, preparing meals became another opportunity to practise English. The group had to agree on ingredients, explain preferences and share jobs in the kitchen. Oliver found these conversations easier than formal classroom discussions because the purpose was clear. If he did not know a particular word, he could describe what he meant or point to an object. The other volunteers did the same. Nobody expected everyone to speak perfectly. Their goal was to understand one another and get dinner ready.",
      "Towards the end of the week, the group walked along one of the routes they had helped clear. It was satisfying to see the result of their work, even though the changes were modest. The organisers explained that conservation was a continuing process and that a single week could not solve every problem. The volunteers' contribution was one part of a larger programme. Oliver returned home with a better understanding of this kind of work and several new friends. He still enjoyed museums and restaurants, but he now knew that a holiday could be valuable for reasons other than the number of attractions visited.",
      "After the holiday, Oliver found that several friends were interested in what he had done. They wanted to know whether a volunteer holiday was suitable for someone without much experience of outdoor work. Oliver explained that the project he had joined provided training and that the organisers did not expect every volunteer to be able to perform every task. However, he advised his friends to read the description of a project carefully before deciding to join. Different organisations could have very different requirements, and a holiday that suited one person might not suit another.",
      "One of his friends, Rachel, said that she liked the idea of helping with nature conservation but was unable to spend a full week away from home. Oliver suggested looking for local opportunities that required less time. They found a small group that organised occasional walks to collect litter from a public path. Rachel decided to attend one event before making a longer commitment. She enjoyed the activity and returned the following month. The experience showed Oliver that contributing to environmental projects did not necessarily require travelling to another country or using an entire holiday.",
      "Oliver also began to think more carefully about the responsibilities of organisations that offered volunteer trips. The programme he had attended was run by people who understood the area and had established plans for the work. The volunteers' activities were connected to those plans. He realised that this connection was important. A group might attract visitors by promising an exciting experience, but its activities would be less useful if they did not address the needs of the place where the work was taking place. He decided that he would ask more questions about the purpose and management of any future programme.",
      "Another issue was the relationship between visitors and local residents. During his holiday, the group had bought some food from nearby shops and followed instructions about which routes to use. The staff had explained that several paths were also important to people living in the area. Volunteers therefore needed to avoid creating unnecessary inconvenience while working. Oliver remembered an occasion when the team had moved tools out of the way so a local walker could pass comfortably. The action was simple, but it reminded him that the forest was not only a destination for people on holiday. It was also part of everyday life for others.",
      "Back at work, Oliver was asked to give a short presentation about his experience to colleagues who were learning English. He decided to focus on the language skills he had used rather than describe every activity. He showed them examples of phrases for asking someone to repeat an instruction, checking that a task had been understood and offering help. These were ordinary expressions, but he had used them more frequently during the holiday than in many of his earlier lessons. He explained that practical situations had given him a clear reason to communicate, even when he was uncertain about his grammar.",
      "Some colleagues wanted to know whether travelling was necessary to develop this kind of confidence. Oliver did not think so. He suggested finding activities in which English had a useful purpose, such as joining a conversation group, working on a shared project with speakers of other languages or following a simple set of instructions in English. The important point was to practise communicating meaning rather than wait until every sentence could be formed perfectly. Formal lessons were still useful because they provided vocabulary and helped learners understand common mistakes. Practical experience gave people a chance to use what they had learned.",
      "When Oliver considered another holiday, he compared two conservation programmes. One was based near a town and offered a mixture of outdoor work and free afternoons. The other involved staying in a remote area with a more demanding daily routine. Both programmes seemed interesting, but he knew that his own preferences and physical abilities would affect his experience. He asked the organisers about accommodation, equipment, rest periods and the support available to new volunteers. He also checked how much the programmes cost and what was included in the price. He wanted to make a decision based on the actual conditions rather than an attractive photograph.",
      "He eventually chose not to book either programme immediately. He planned to take a few shorter trips closer to home first and continue with the local environmental group whenever his schedule allowed. He was pleased that the previous holiday had introduced him to something he could enjoy throughout the year. His interest in cities had not disappeared, and he still wanted to visit museums and try food in new places. The difference was that he no longer felt that every holiday had to follow the same pattern. A good holiday could provide rest, enjoyment, useful work, learning or a combination of these things, depending on what a person needed at that time."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Why was the work hard at first?",
        "options": [
          "The volunteers had no equipment.",
          "Oliver was not used to early mornings.",
          "He could not speak any English."
        ],
        "answer": 1,
        "evidence": "Oliver was not used to getting up early."
      },
      {
        "type": "true_false",
        "prompt": "Most volunteers were native English speakers.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Most were not native speakers."
      },
      {
        "type": "choice",
        "prompt": "Why did his English confidence improve?",
        "options": [
          "He used English for practical communication.",
          "He attended daily grammar lessons.",
          "Everyone spoke his first language."
        ],
        "answer": 0,
        "evidence": "He needed to use it for real tasks rather than classroom exercises."
      },
      {
        "type": "choice",
        "prompt": "How does Oliver feel about city holidays now?",
        "options": [
          "He refuses to visit cities again.",
          "He has never enjoyed them.",
          "He still enjoys them."
        ],
        "answer": 2,
        "evidence": "He still enjoys visiting cities."
      },
      {
        "type": "true_false",
        "prompt": "The conservation project lasted a week.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "He joined a week-long conservation project."
      },
      {
        "type": "choice",
        "prompt": "What did the organisers provide for beginners?",
        "options": [
          "Luxury hotel rooms",
          "Guaranteed wildlife encounters",
          "Training and basic accommodation"
        ],
        "answer": 2,
        "evidence": "The project offered basic accommodation and training for beginners."
      },
      {
        "type": "choice",
        "prompt": "Why did the group record the parts of the path it had checked?",
        "options": [
          "To compete against other teams",
          "To help identify where further work was needed",
          "To calculate the price of their accommodation"
        ],
        "answer": 1,
        "evidence": "The records helped the organisers decide where more work was needed."
      },
      {
        "type": "choice",
        "prompt": "What does Oliver's friend Rachel do instead of a week-long volunteer holiday?",
        "options": [
          "She books a remote trip immediately",
          "She stops volunteering altogether",
          "She joins a local litter collection event"
        ],
        "answer": 2,
        "evidence": "Rachel decided to attend one event before making a longer commitment."
      },
      {
        "type": "true_false",
        "prompt": "The volunteers divided tasks according to their abilities.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "They learned to divide the tasks according to what each person could comfortably do."
      },
      {
        "type": "true_false",
        "prompt": "Oliver believes that travelling abroad is necessary to practise meaningful English communication.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Oliver did not think so. He suggested finding activities in which English had a useful purpose, such as joining a conversation group, working on a shared project with speakers of other languages or following a simple set of instructions in English."
      }
    ]
  },
  {
    "id": "b1-03",
    "level": "B1",
    "title": "Starting a school podcast",
    "titleUk": "Шкільний подкаст",
    "paragraphs": [
      "A group of students wanted to create a podcast about life at their school. Their first recording was almost an hour long and included several interruptions. After listening back, they realised that a shorter episode with a clear plan would be easier to follow. They divided the work: one student interviewed guests, another edited the audio, and two others prepared questions and checked facts.",
      "Their first published episode was about the school sports club. It received fewer listeners than expected, but comments from classmates suggested that the interviews were useful. The team decided to invite listeners to send questions for future episodes. They also made written summaries so that students who could not listen could still access the information. Within two months, the podcast had become a regular part of school life. The team learned that improving a project often matters more than getting everything right immediately.",
      "The idea for the podcast began during a discussion about school announcements. Students complained that they sometimes missed information about clubs or events because notices were easy to overlook. A teacher suggested that the group experiment with a short audio programme. The students decided that the programme should be made by students and cover topics that were genuinely useful to their classmates. They did not need expensive equipment at the beginning; the school already had a quiet room and a basic microphone they could borrow.",
      "Their first recording was exciting to make but difficult to listen to. Several speakers talked at the same time, and background noise made some answers hard to understand. The students had also included unrelated conversations because they did not have a clear plan. When they listened to the recording together, they agreed that a listener who did not know them might lose interest quickly. They wrote down the main problems and decided to try a simpler format.",
      "For the next episode, the team prepared an introduction, three main questions and a short ending. They chose a topic that could be explained in about ten minutes. The interviewer contacted the sports club in advance and asked for permission to record a short conversation. Another student checked the meeting times and other details with the club organiser. The editor removed long pauses but kept the meaning of the answers unchanged. They also agreed that nobody's voice would be published without permission.",
      "When the episode appeared, the team expected nearly everyone in their year to listen. In reality, only a small number of people responded during the first few days. At first the students felt disappointed, but the teacher asked them to examine the feedback rather than focus only on the number of listeners. Several classmates said that the interview had helped them understand how to join the sports club. One student suggested adding information about clubs that were suitable for beginners.",
      "The team created a way for listeners to submit questions. They selected topics that several people had asked about and invited guests who could give reliable answers. They kept a simple schedule so that each person knew what to do before a recording. Written summaries became particularly useful when students wanted to check a time or location without listening to the whole episode again. The summaries also helped students who preferred to read information or could not use audio at a particular moment.",
      "Two months later, the team held a meeting to review the project. Their recordings were clearer and their topics more focused, but they still had challenges. Editing took time, and sometimes guests had to cancel. The students prepared a few short episodes in advance so they could continue when someone was busy with exams. They also decided not to publish an episode unless the information had been checked. They had learned that a successful podcast required cooperation, planning and responsibility, not just the ability to talk into a microphone. The project became a place where students could practise communication skills while doing something useful for their school.",
      "As the school podcast developed, the students discovered that choosing topics was not always straightforward. They had received suggestions about sports, school meals, homework and several events that had not yet been announced. Some listeners wanted the podcast to cover everything that interested them, but the team had limited time and could not prepare a reliable episode about every suggestion. They decided to make a shared list of possible topics and discuss which ones could be covered with the resources they had. They gave priority to questions that were useful to many students or particularly relevant at that time.",
      "For an episode about school clubs, they contacted several club leaders before deciding which guests to interview. They wanted to avoid giving the impression that only the largest or most popular clubs mattered. A smaller art club, for example, offered activities that some students knew little about. The team invited its organiser to explain how beginners could take part. They also interviewed a student who had joined the club without much previous experience. The interview helped listeners understand what attending the club would actually be like, rather than simply hear a list of meeting times.",
      "Preparing good questions became an important skill for the interviewer. At first, the questions were often so broad that guests did not know where to begin. Asking someone to describe everything about a club could lead to a long answer containing many details that were not relevant to a new student. The team learned to ask more specific questions, such as what a visitor should bring to their first meeting or whether previous experience was necessary. They also prepared follow-up questions but remained flexible enough to explore an interesting answer that they had not expected.",
      "Another challenge involved checking information. A guest once mentioned that a meeting took place on a particular day, but the timetable had changed recently. Before publishing the recording, one of the team members noticed that the information did not match the latest notice. They contacted the organiser and confirmed the correct day. The editor removed the outdated statement and added a short explanation with the updated information. This incident showed why checking facts was an essential part of the project, even when the guest had spoken sincerely and had no intention of giving incorrect information.",
      "The team also established a process for dealing with corrections after publication. They decided that if an episode contained an important error, they would update the written summary and add a clear correction where listeners could find it. They did not want to remove a mistake quietly and leave people who had already heard the episode with the wrong information. The teacher explained that being willing to correct an error was a sign of responsibility. The students agreed that accuracy was more important than pretending their work was perfect.",
      "As their audience grew, some students suggested making the programme longer and publishing it more frequently. The team discussed these ideas but decided that a regular, manageable schedule was better than promising more than they could deliver. Each member had schoolwork and other commitments. Editing an episode could take several hours, especially when the sound quality was poor. They began keeping a record of how long different tasks took. This helped them plan ahead and avoid asking one person to do most of the work whenever a deadline approached.",
      "They also considered how new members could join the team. If only the original students knew how to record and edit episodes, the podcast might stop when they became busy or left the school. The students wrote a short guide covering the main stages of production. It explained how to agree on a topic, obtain permission to record, prepare questions, check information and publish a summary. They invited two younger students to observe a recording and try some of the simpler tasks. The younger students brought new ideas and eventually helped prepare an episode of their own.",
      "At the end of the term, the team reviewed the original reason for starting the podcast. They had wanted to make school information easier to find and help students learn about activities they might otherwise miss. They looked at comments from listeners and considered which episodes had been particularly useful. They also discussed which kinds of information were better provided in a short written notice than in a recording. A podcast was not the best format for every message, and accepting that limitation helped them use it more effectively. They were proud of the programme, but they understood that its value depended on whether it continued to meet a genuine need. Their next aim was to make it easier for future students to contribute without losing the standards they had established."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What did the students change after their first recording?",
        "options": [
          "They planned shorter, clearer episodes.",
          "They stopped interviewing people.",
          "They recorded only music."
        ],
        "answer": 0,
        "evidence": "A shorter episode with a clear plan would be easier to follow."
      },
      {
        "type": "choice",
        "prompt": "Why did they make written summaries?",
        "options": [
          "To replace all audio episodes",
          "To test the sports club",
          "To make information accessible without listening"
        ],
        "answer": 2,
        "evidence": "So that students who could not listen could still access the information."
      },
      {
        "type": "choice",
        "prompt": "What lesson did the team learn?",
        "options": [
          "Audience questions are not useful.",
          "Projects can improve through feedback and revision.",
          "A project must be perfect before anyone sees it."
        ],
        "answer": 1,
        "evidence": "Improving a project often matters more than getting everything right immediately."
      },
      {
        "type": "true_false",
        "prompt": "The first published episode covered the sports club.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Their first published episode was about the school sports club."
      },
      {
        "type": "true_false",
        "prompt": "The first episode attracted more listeners than expected.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "It received fewer listeners than expected."
      },
      {
        "type": "choice",
        "prompt": "Why did the students originally consider a podcast?",
        "options": [
          "Their teacher wanted longer lessons",
          "School announcements were easy to miss",
          "The school had no sports clubs"
        ],
        "answer": 1,
        "evidence": "Students complained that they sometimes missed information about clubs or events because notices were easy to overlook."
      },
      {
        "type": "choice",
        "prompt": "What did the editor preserve while removing pauses?",
        "options": [
          "The meaning of the answers",
          "The original recording length",
          "Every piece of background noise"
        ],
        "answer": 0,
        "evidence": "The editor removed long pauses but kept the meaning of the answers unchanged."
      },
      {
        "type": "choice",
        "prompt": "Why does the team write a guide to podcast production?",
        "options": [
          "To replace every recording with an advertisement",
          "To prevent new members from joining",
          "To help future members learn the process"
        ],
        "answer": 2,
        "evidence": "It explained how to agree on a topic, obtain permission to record, prepare questions, check information and publish a summary."
      },
      {
        "type": "true_false",
        "prompt": "The team obtained permission before publishing someone's voice.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "They also agreed that nobody's voice would be published without permission."
      },
      {
        "type": "true_false",
        "prompt": "The team decides to remove published mistakes quietly without telling listeners.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "They did not want to remove a mistake quietly and leave people who had already heard the episode with the wrong information."
      }
    ]
  },
  {
    "id": "b1-04",
    "level": "B1",
    "title": "A shared community space",
    "titleUk": "Спільний простір для громади",
    "paragraphs": [
      "An unused building in a small town stood empty for several years. Local residents suggested turning it into a community centre, but they disagreed about what it should offer. Teenagers wanted a place to study, parents asked for activities for children, and older residents wanted a meeting room. Rather than choosing one group, the organisers created a timetable that allowed different people to use the same rooms at different times.",
      "The first months were difficult because volunteers had to clean the building and find affordable furniture. A local business donated tables, and residents brought books and board games. The centre now runs free language exchanges, homework sessions and craft workshops. Although it cannot meet every request, the organisers review the schedule each month. The project shows how listening to different needs can turn an empty space into something valuable for many people.",
      "The building had once been used as a local office, but it was no longer needed. Its windows were dusty, and the rooms had been empty for so long that many residents had stopped noticing it. A small group of neighbours contacted the town council to ask whether the building could be used for community activities. The council was interested but wanted to know who would manage it, how the costs would be covered and how the space would remain safe and accessible.",
      "At the first public meeting, there were more suggestions than the organisers could write down. Some people wanted a permanent library, others suggested exercise classes, and several residents hoped to start a place where children could do homework after school. There were also people who worried about noise and increased traffic. The organisers made notes and invited residents who could not attend to send written comments. They wanted to understand the needs of the whole area, not just the people who were able to come to the meeting.",
      "The next step was to examine the building with people who had the appropriate experience. They identified repairs that needed professional attention and smaller jobs that volunteers could help with. The organisers collected estimates for essential work and prepared a simple budget. They decided to open only the rooms that were ready for use instead of trying to complete the entire building at once. This allowed them to test whether people would actually attend the activities before spending more money.",
      "When the first room opened, the timetable was quite simple. Students could use it for quiet study after school on certain days, and a group of older residents met there in the morning. At weekends, volunteers organised small workshops. A local business provided tables, while families donated books, games and other useful materials. Everything was checked before it was put into the room. Items that were damaged or unsuitable were not accepted just because someone had offered them for free.",
      "As more people began using the centre, problems appeared. One group wanted to extend its meeting into the time reserved for another group. A popular craft activity needed more space than expected. The organisers created a booking system and asked each activity leader to leave the room ready for the next group. They also set aside a small amount of time each week for cleaning. The aim was to make sharing the space practical rather than expect every disagreement to disappear.",
      "The language exchange became one of the most successful activities. People with different first languages met to practise short conversations and help each other. Some participants later offered to run other workshops. Homework sessions also attracted regular visitors, although attendance changed during school holidays. The organisers reviewed their timetable each month and moved activities when necessary. They made sure that the most popular groups did not automatically receive all the available time. The centre could not provide everything that residents wanted, but it had become a place where different generations could meet and where new ideas could be tested without requiring each group to find its own building.",
      "As the community centre became more established, the organisers discovered that opening the building was only the beginning of their responsibilities. Every activity required someone to arrange the room, welcome visitors and make sure that the space was left in good condition. The building also needed regular cleaning, heating and occasional repairs. At first, several enthusiastic volunteers tried to deal with most of these tasks themselves. After a few months, however, they realised that this arrangement would be difficult to maintain. People had jobs, families and other responsibilities, and a project could not depend indefinitely on the same small group.",
      "The organisers created a list of tasks that volunteers could choose from. Some jobs required particular experience, while others involved simple activities such as arranging chairs or preparing information for visitors. They made sure that people understood what was expected before agreeing to help. A resident who was unable to attend regularly offered to prepare printed notices at home. Another person volunteered to check the supply of materials once a month. These contributions were less visible than running a popular workshop, but they helped the centre operate smoothly.",
      "Money was another subject that required careful attention. Although the centre offered many activities free of charge, the costs of maintaining the building did not disappear. The council contributed to some essential expenses, and local residents sometimes made small donations. The organisers prepared a basic financial report showing how money had been received and spent. They hoped that this would help people understand why some requests could not be met immediately. If a new activity needed expensive equipment, the group first considered whether it could borrow suitable items or share them with another organisation.",
      "One disagreement arose when a group proposed turning a room into a permanent art studio. The room was already used by students who needed a quiet place to study, and the organisers did not want to remove that activity without considering the consequences. They met with representatives of both groups to discuss their needs. The art group explained that moving equipment before and after every workshop took a long time. The students explained that they needed predictable access to desks in the afternoon. Both concerns were reasonable, but the building did not have enough space to give each group an entirely separate room.",
      "The solution was to change the storage arrangements rather than choose between the two activities. The organisers found some suitable cupboards where art materials could be stored safely. They agreed on a timetable that provided longer periods for art workshops on selected days and quiet study on other afternoons. Neither group received everything it had originally requested, but both could continue using the centre. After a few weeks, the organisers asked the participants whether the arrangement was working. They made a small adjustment when they discovered that one workshop needed more time for cleaning at the end.",
      "The centre also tried to include people who had not attended the original public meetings. Some residents did not know that activities were open to beginners, while others were unsure whether they would feel comfortable in a new group. Volunteers prepared clear descriptions of the activities, including information about their cost, expected length and any materials that participants should bring. They offered a few introductory sessions where visitors could ask questions before deciding whether to join a regular group. This helped people make choices based on actual information rather than assumptions about who the centre was intended for.",
      "The organisers paid attention to attendance, but they did not judge every activity solely by the number of participants. A homework session with a few students might provide important help even if it was smaller than a popular weekend event. A language exchange might need different arrangements when beginners and more confident speakers attended together. The organisers considered both the purpose of an activity and the resources it required. They asked activity leaders to describe what was working well and what difficulties they had encountered. The monthly timetable review gradually became a way to improve the programme rather than simply move activities from one time to another.",
      "After a year, the community centre looked very different from the empty building the residents had first discussed. It was not perfect, and there were still limits on the space, money and number of volunteers available. Nevertheless, people had developed a practical way of sharing responsibility for it. Residents who had rarely spoken to one another were now meeting through different activities. Several groups had begun cooperating on small projects. The organisers recognised that the centre's success did not depend on making everyone agree about every decision. It depended on having a fair process for considering requests, explaining limitations and finding solutions when different needs competed for the same resources."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "How did the organisers handle different requests?",
        "options": [
          "They chose only teenagers’ activities.",
          "They built three new centres.",
          "They created a shared timetable."
        ],
        "answer": 2,
        "evidence": "The organisers created a timetable that allowed different people to use the same rooms at different times."
      },
      {
        "type": "choice",
        "prompt": "Who donated tables?",
        "options": [
          "The town’s children",
          "A local business",
          "A school abroad"
        ],
        "answer": 1,
        "evidence": "A local business donated tables."
      },
      {
        "type": "choice",
        "prompt": "What makes the project valuable?",
        "options": [
          "It responds to different community needs.",
          "It charges high fees for activities.",
          "It provides one activity for everyone."
        ],
        "answer": 0,
        "evidence": "Listening to different needs can turn an empty space into something valuable for many people."
      },
      {
        "type": "true_false",
        "prompt": "The centre can meet every request.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "It cannot meet every request."
      },
      {
        "type": "true_false",
        "prompt": "The schedule is reviewed each month.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "The organisers review the schedule each month."
      },
      {
        "type": "choice",
        "prompt": "Why did the organisers initially open only some rooms?",
        "options": [
          "To test demand before further spending",
          "To exclude teenagers permanently",
          "To store all the donated furniture"
        ],
        "answer": 0,
        "evidence": "This allowed them to test whether people would actually attend the activities before spending more money."
      },
      {
        "type": "choice",
        "prompt": "How did they manage competing demands for rooms?",
        "options": [
          "They let the first group keep the room all day",
          "They removed all group activities",
          "They created a booking system"
        ],
        "answer": 2,
        "evidence": "The organisers created a booking system and asked each activity leader to leave the room ready for the next group."
      },
      {
        "type": "choice",
        "prompt": "How does the centre address the disagreement over a permanent art studio?",
        "options": [
          "By improving storage and sharing the room at different times",
          "By ending all art activities",
          "By removing quiet study from the centre"
        ],
        "answer": 0,
        "evidence": "The solution was to change the storage arrangements rather than choose between the two activities."
      },
      {
        "type": "true_false",
        "prompt": "Residents unable to attend the meeting could send written comments.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "The organisers made notes and invited residents who could not attend to send written comments."
      },
      {
        "type": "true_false",
        "prompt": "The centre judges every activity solely by its attendance.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "The organisers paid attention to attendance, but they did not judge every activity solely by the number of participants."
      }
    ]
  },
  {
    "id": "b1-05",
    "level": "B1",
    "title": "The value of a mistake",
    "titleUk": "Цінність помилки",
    "paragraphs": [
      "During a cooking competition, Hannah accidentally added twice as much lemon juice to her sauce as the recipe required. She wanted to throw the mixture away, but there was not enough time to start again. Her teammate suggested tasting the sauce and balancing the flavour with other ingredients. After several small adjustments, they created a sauce that was different from the original recipe but still tasted good.",
      "The judges praised their ability to adapt, although they did not win the competition. Hannah used to believe that following instructions exactly was the only way to succeed. The experience taught her that understanding the purpose of each step can be just as important. She now experiments more often when cooking at home. However, she still follows safety instructions carefully, because some rules are not simply a matter of taste. The mistake became a useful lesson in when to be flexible and when to be precise.",
      "Hannah had spent several weeks preparing for the competition. Her team had practised making the same dish until everyone knew the order in which the ingredients should be prepared. On the day, however, they were working in an unfamiliar kitchen. The equipment was arranged differently, and they had to share some of the space with other teams. Hannah was responsible for the sauce while her teammate prepared the main dish. They had agreed to communicate whenever one part of the meal was delayed.",
      "When Hannah noticed her mistake, her first reaction was to imagine the judges tasting a sauce that was far too sour. She worried that the team's weeks of practice had been wasted. Her teammate asked her to explain what had happened. Together they compared the amount of lemon juice with the original recipe. Since there was not enough time to start again, they decided to work with the mixture they already had, provided that it remained safe to serve.",
      "They took a small amount of sauce into a separate bowl and tested a possible adjustment before changing the entire mixture. The first attempt did not improve the flavour enough. A second small adjustment made a more noticeable difference. They tasted again and discussed whether the new flavour would work with the rest of the dish. This method allowed them to learn from each change without risking the whole sauce at once. They recorded the approximate amounts they had used so that they could remember what had worked.",
      "Meanwhile, they had to keep an eye on the time. Hannah's teammate continued preparing the main dish while Hannah finished the sauce. They decided not to change the presentation at the last minute, because that would create another problem. Instead, they served the dish they had prepared, with the revised sauce. When the judges asked about it, Hannah explained what had happened. The team did not pretend that the sauce was exactly the one they had intended to make.",
      "After the competition, Hannah reviewed her notes. She noticed that she had measured the lemon juice while thinking about another task. In future she planned to measure important ingredients before starting and keep them in clearly marked containers. This was a practical improvement rather than simply telling herself to be more careful. She also thought about the way her teammate had reacted. Instead of blaming her, the teammate had helped identify the problem and find a possible solution.",
      "Hannah began applying this approach at home. When trying a new recipe, she still read the instructions and followed them closely the first time. Once she understood how the dish worked, she felt more comfortable changing the flavour. She knew that some instructions, such as those related to food hygiene and safe cooking, were different from personal preferences about taste. She did not treat safety rules as opportunities for experiments. What she had learned was not that mistakes were always useful, but that a mistake could become useful if it was noticed, investigated and corrected. The experience also reminded her that cooperation could matter more than finding someone to blame.",
      "In the months after the competition, Hannah became interested in the way people respond to mistakes in other situations. At school, she noticed that students sometimes tried to hide an error in their homework because they were worried about receiving a low mark. In group projects, a person who had forgotten a task might avoid telling the others until the deadline was very close. These reactions were understandable, but they could make a problem harder to solve. Hannah remembered that her teammate had been able to help because she had explained the mistake as soon as she noticed it.",
      "During a science project, Hannah worked with several classmates who were preparing a simple presentation. One student realised that they had copied a figure incorrectly from their notes. The mistake affected a chart that the group had already completed. Instead of arguing about who was responsible, they checked the original information and corrected the chart. They also reviewed the other figures in case a similar mistake had been made elsewhere. The correction took time, but it was much easier to complete before the presentation than it would have been after showing inaccurate information to the class.",
      "Hannah began to distinguish between different kinds of mistakes. Some happened because a person did not understand the task. Others occurred even when the person knew what to do but was distracted, tired or working in a hurry. A mistake could also result from unclear instructions or a process that made it easy to confuse two similar items. These differences mattered because the best way to prevent the same problem depended on its cause. Providing more information might help someone who did not understand a task, but it would not necessarily solve a problem caused by a confusing arrangement of materials.",
      "She applied this idea when practising a new recipe at home. Several ingredients looked similar when placed in small bowls, so she began adding simple labels and putting them in the order in which they would be used. She kept the recipe nearby and checked it before adding each important ingredient. These habits did not require her to become a completely different person or remember every instruction perfectly. They made it easier to notice a possible mistake before it affected the dish. She found that organising the task well was often more useful than relying on concentration alone.",
      "There were also occasions when flexibility was the wrong response. One afternoon, a friend suggested using an ingredient that had been stored in uncertain conditions because they did not want to waste it. Hannah explained that they should not take a risk with food safety simply to finish a recipe. They chose another meal instead. She understood that the lesson from the competition was about adapting within appropriate limits, not finding a way to continue regardless of the circumstances. Sometimes stopping was the responsible decision, even when it meant accepting that the original plan could not be completed.",
      "When the next cooking competition was announced, Hannah and her teammate decided to enter again. They reviewed their previous experience and made a simple plan for preparing the ingredients. They discussed what each person would be responsible for and how they would communicate if something went wrong. They also agreed that they would allow enough time to check the final dish before serving it. The plan did not include instructions for every possible problem, because they could not predict everything that might happen. Instead, it gave them a reliable way to organise their work and respond if a difficulty appeared.",
      "During their practice sessions, the team deliberately experimented with different flavours in small portions of food. They compared the results and wrote down what they had changed. Sometimes the original recipe tasted better, and sometimes a small adjustment improved it. The important difference was that these experiments were planned. The students could observe what happened without putting an entire meal at risk. Hannah realised that practising flexibility in a controlled situation could make it easier to remain calm when an unexpected problem occurred during a real task.",
      "Before the competition, their teacher asked the students what they hoped to achieve. Hannah wanted to prepare a good dish and would have been pleased to win, but she also wanted to see whether the team's new way of working was effective. She no longer judged the value of a task entirely by the final result. A successful performance could still contain weaknesses that needed attention, while an unsuccessful performance could reveal useful information about what to improve. She understood that a mistake was not automatically a valuable experience. It became valuable when someone took responsibility for it, investigated the causes and used what they learned to make better decisions in the future. This attitude helped her approach both cooking and schoolwork with greater confidence."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Why did Hannah not start again?",
        "options": [
          "Her teammate had left.",
          "There was not enough time.",
          "The judges forbade it."
        ],
        "answer": 1,
        "evidence": "There was not enough time to start again."
      },
      {
        "type": "true_false",
        "prompt": "They did not win the competition.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "They did not win the competition."
      },
      {
        "type": "choice",
        "prompt": "What did the judges praise?",
        "options": [
          "Their ability to adapt",
          "Their exact use of the recipe",
          "Their speed in washing dishes"
        ],
        "answer": 0,
        "evidence": "The judges praised their ability to adapt."
      },
      {
        "type": "choice",
        "prompt": "Which rules does Hannah still follow carefully?",
        "options": [
          "All flavour suggestions",
          "Only time limits",
          "Safety instructions"
        ],
        "answer": 2,
        "evidence": "She still follows safety instructions carefully."
      },
      {
        "type": "true_false",
        "prompt": "They threw the original mixture away.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "They created a sauce that was different from the original recipe."
      },
      {
        "type": "choice",
        "prompt": "Why did Hannah test adjustments in a separate bowl?",
        "options": [
          "To make a second dish for judges",
          "To hide the error from her teammate",
          "To avoid risking the entire sauce"
        ],
        "answer": 2,
        "evidence": "This method allowed them to learn from each change without risking the whole sauce at once."
      },
      {
        "type": "choice",
        "prompt": "What did she plan to do differently before cooking in future?",
        "options": [
          "Use more lemon juice",
          "Measure important ingredients in advance",
          "Change every recipe immediately"
        ],
        "answer": 1,
        "evidence": "In future she planned to measure important ingredients before starting and keep them in clearly marked containers."
      },
      {
        "type": "choice",
        "prompt": "Why does Hannah begin labelling ingredients during practice?",
        "options": [
          "To use more ingredients",
          "To avoid reading the recipe",
          "To make it easier to detect a possible error"
        ],
        "answer": 2,
        "evidence": "They made it easier to notice a possible mistake before it affected the dish."
      },
      {
        "type": "true_false",
        "prompt": "The teammate helped solve the problem rather than blame Hannah.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Instead of blaming her, the teammate had helped identify the problem and find a possible solution."
      },
      {
        "type": "true_false",
        "prompt": "Hannah and her friend decide to use an ingredient stored in uncertain conditions to avoid waste.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "They chose another meal instead."
      }
    ]
  },
  {
    "id": "b1-06",
    "level": "B1",
    "title": "Studying in a group",
    "titleUk": "Навчання в групі",
    "paragraphs": [
      "Before an important history exam, Ben and three classmates decided to study together. At their first meeting, they spent more time chatting than reviewing their notes. Ben suggested that each person prepare a short explanation of one topic and then ask the others questions. The new method made their meetings more focused. If someone could not answer, the group discussed the topic rather than simply giving the correct response.",
      "Ben also discovered that explaining a topic revealed gaps in his own knowledge. He began to notice which ideas he understood and which he had only memorised. However, the group did not replace individual study. Each member still reviewed their own notes and completed practice questions alone before meeting. After the exam, they agreed that the combination of independent preparation and group discussion had helped them feel more confident.",
      "The students had originally planned to meet twice a week in the school library. They each brought a textbook and several pages of notes. At the first meeting, they opened their books and started talking about the exam. Soon the conversation moved to other subjects, and nobody was sure what they were supposed to have learned by the end of the session. Ben realised that having other people around was not enough to make a study session effective. They needed a shared purpose.",
      "Before the second meeting, each student selected one historical event from the topics they had been given. They prepared a short explanation covering what had happened, why it mattered and how it was connected to other events. Ben chose a topic that he thought he understood well. When he tried to explain it without reading his notes, he discovered that he could remember several dates but could not clearly describe the reasons behind the event. He went back to the textbook and checked the missing information.",
      "At the meeting, the students took turns presenting their topics. The others asked questions, and the speaker tried to answer without looking at the book immediately. If nobody knew an answer, they wrote down the question and checked it together. They agreed not to guess when they could find a reliable explanation in their course materials. This helped them avoid sharing incorrect information and gave each student a list of things to review before the next meeting.",
      "They also discovered that different students had different strengths. One remembered dates easily, another was good at explaining the connection between events, and a third could organise information into a clear timeline. Instead of expecting everyone to study in the same way, they used these strengths to support one another. The timeline was particularly helpful when two events had similar names and the students kept confusing them. They drew it on a sheet of paper and added short explanations beside the dates.",
      "As the exam approached, the group began to practise questions under a time limit. Each student answered independently before discussing the results. This was important because a discussion could create the impression that everyone understood a topic, even when some people were simply following the explanations of others. Ben found that he often recognised a correct answer when he saw it but had difficulty producing the same answer on his own. Independent practice helped him notice this difference.",
      "The group decided to keep their final meeting shorter than usual. They reviewed the questions that had caused the most difficulty and then went home to rest. After the exam, they compared their experiences without worrying about who had received the highest mark. They agreed that the method had been helpful, although some topics still required more individual practice. Ben decided to use a similar approach in other subjects. He would prepare alone, explain important ideas to someone else when possible, and then test his own understanding without help. The group had shown him that studying together worked best when it encouraged active thinking rather than replaced it.",
      "After the history exam, Ben and his classmates decided to try the same method for a different subject. They chose science because several of them found it difficult to explain processes that involved more than one stage. Before their first meeting, they discussed how the new subject differed from history. Remembering dates and organising events into a timeline had been useful in history, but science often required understanding relationships between concepts. They agreed that their study methods should match the type of knowledge they were trying to develop rather than follow exactly the same routine every time.",
      "Each student prepared a diagram or a short explanation of one topic. Ben chose a process that he had seen illustrated in his textbook. He could recognise the diagram when it was in front of him, but when he tried to draw it from memory, he left out an important stage. He checked his notes and practised explaining why the missing stage mattered. At the group meeting, he asked the others to reconstruct the process on a blank piece of paper. They compared their diagrams and discussed the differences. This helped them discover which parts of the topic they understood and which parts they had merely become familiar with.",
      "The group also considered the problem of giving one another feedback. At first, a student who knew an answer sometimes corrected someone immediately, before that person had finished speaking. The students realised that this could prevent the speaker from noticing their own mistake. They agreed to give each person a little time to complete an explanation. If an answer was incomplete, they would first ask a question that encouraged the speaker to think about the missing part. They could then check the answer together. This approach made the discussions more supportive without requiring the group to accept incorrect information.",
      "Another challenge was choosing suitable practice questions. If the students repeated the same questions every time, their scores might improve because they remembered the answers rather than because they understood the material. They began using questions with slightly different examples that required the same underlying knowledge. For some topics, they asked each person to create a new question and explain the answer. They checked that the questions were clear and that the information could be verified from their course materials. The activity helped them think about what an exam question was actually testing.",
      "Ben discovered that short reviews on different days were often more useful than trying to study everything during one long session. He made a list of topics that he found difficult and returned to them after a few days. Instead of reading his notes from beginning to end each time, he tried to answer a question first and then checked the relevant section. When he could explain an idea accurately after a delay, he felt more confident that he had learned it. If he had forgotten something, he wrote down what needed more attention and arranged another review.",
      "Not every group meeting was equally productive. During one busy week, two members arrived without having prepared their topics. The group spent much of the session reading silently and did not have enough time for discussion. Ben suggested that they choose shorter preparation tasks when everyone had several deadlines. They also agreed that a meeting could be cancelled or shortened if most members were unable to prepare. The purpose was to help people learn, not simply maintain a schedule regardless of whether the sessions were useful.",
      "The students paid attention to the different circumstances of their classmates. One member could not always stay after school because of responsibilities at home. The others shared a short summary of the key questions so that the student could review them independently. They sometimes arranged a brief discussion during lunch instead of a longer meeting in the afternoon. They understood that a shared study routine needed to be flexible enough to work for the people taking part. Otherwise, the group might become another source of pressure rather than a helpful way to prepare.",
      "By the end of the term, Ben had developed a more deliberate approach to studying. He began by identifying what he needed to know, chose a suitable activity and then checked whether he could produce an answer without relying on his notes. He used group discussions when they allowed him to hear different explanations or practise communicating a difficult idea. He continued studying alone when he needed to concentrate or measure his own understanding. The combination was useful because each method addressed a different need. Ben realised that the most effective part of the group had not been the fact that several students sat in the same room. It had been their willingness to prepare, ask questions, examine mistakes and take responsibility for their own learning."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What problem did the first meeting have?",
        "options": [
          "They chatted more than they studied.",
          "Nobody brought a history book.",
          "They studied for too many hours."
        ],
        "answer": 0,
        "evidence": "They spent more time chatting than reviewing their notes."
      },
      {
        "type": "choice",
        "prompt": "What did explaining topics help Ben identify?",
        "options": [
          "The exact exam questions",
          "Other students’ grades",
          "Gaps in his own understanding"
        ],
        "answer": 2,
        "evidence": "Explaining a topic revealed gaps in his own knowledge."
      },
      {
        "type": "choice",
        "prompt": "Which study method did the group prefer in the end?",
        "options": [
          "Only memorising notes",
          "Independent preparation plus discussion",
          "Only group meetings"
        ],
        "answer": 1,
        "evidence": "The combination of independent preparation and group discussion had helped them feel more confident."
      },
      {
        "type": "true_false",
        "prompt": "The group simply gave answers whenever someone struggled.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "The group discussed the topic rather than simply giving the correct response."
      },
      {
        "type": "true_false",
        "prompt": "Each member prepared independently as well.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Each member still reviewed their own notes and completed practice questions alone."
      },
      {
        "type": "choice",
        "prompt": "What did Ben discover when explaining his first topic?",
        "options": [
          "He already understood every detail",
          "He knew dates but lacked a clear explanation of causes",
          "He had memorised no dates at all"
        ],
        "answer": 1,
        "evidence": "He discovered that he could remember several dates but could not clearly describe the reasons behind the event."
      },
      {
        "type": "choice",
        "prompt": "How did the group handle a question that nobody could answer?",
        "options": [
          "They wrote it down and checked together",
          "They removed the topic from their notes",
          "They selected an answer at random"
        ],
        "answer": 0,
        "evidence": "If nobody knew an answer, they wrote down the question and checked it together."
      },
      {
        "type": "choice",
        "prompt": "Why does the group begin using questions with different examples?",
        "options": [
          "To avoid studying difficult topics",
          "To test knowledge rather than memory of the exact answers",
          "To make it impossible to compare explanations"
        ],
        "answer": 1,
        "evidence": "If the students repeated the same questions every time, their scores might improve because they remembered the answers rather than because they understood the material."
      },
      {
        "type": "true_false",
        "prompt": "The group made a timeline to distinguish similar events.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "The timeline was particularly helpful when two events had similar names and the students kept confusing them."
      },
      {
        "type": "true_false",
        "prompt": "The students insist on holding every meeting even when most people cannot prepare.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "They also agreed that a meeting could be cancelled or shortened if most members were unable to prepare."
      }
    ]
  },
  {
    "id": "b2-01",
    "level": "B2",
    "title": "The hidden cost of convenience",
    "titleUk": "Прихована ціна зручності",
    "paragraphs": [
      "A grocery delivery service promises customers more time for the things they value. For a busy parent, this may be a genuine benefit: a weekly shop can be completed in minutes rather than requiring a journey across town. For other customers, however, convenience can gradually change their spending habits. Small purchases that once seemed too inconvenient to justify become effortless, particularly when an app encourages users to order with a single tap.",
      "The service itself is not necessarily the problem. Delivery can improve access for people who have limited mobility or live far from shops. The issue is whether users understand the trade-offs they are making. A low delivery fee, for example, might conceal additional packaging, minimum order requirements or slightly higher product prices. Comparing the total cost with an ordinary shop is more informative than looking at the advertised fee alone.",
      "Rather than rejecting convenient technology, consumers can benefit from using it deliberately. Planning orders, checking receipts and setting a budget may allow them to enjoy the advantages without developing costly habits. Convenience is valuable, but its value depends on how it is used.",
      "Imagine two households using the same delivery service. The first consists of a couple who work irregular hours and care for a relative. Before using the service, one of them often spent part of the weekend travelling to a supermarket. Ordering groceries in advance allows them to coordinate meals and avoid an inconvenient journey. The second household is close to several shops and has no significant transport difficulties. Its members begin ordering whenever they notice that an ingredient is missing. Both households benefit from convenience, but the effect on their routines and budgets may be quite different.",
      "This difference is important because convenience is not a single, measurable benefit. A service may save time while increasing expenditure, or reduce physical effort while requiring more planning. For a person with a disability, the ability to order independently can be more significant than the advertised saving in minutes. For somebody who already walks past a supermarket every day, the same service might remove very little effort. Evaluating a service requires understanding the circumstances in which it is used rather than assuming that its advantages are identical for every customer.",
      "Digital interfaces also influence the decisions people make. A suggested shopping list can be helpful when it reminds a customer to purchase something they regularly need. The same feature can encourage additional spending when it includes products that are merely similar to previous purchases. Notifications about special offers may create a sense of urgency, even when the customer has no immediate need for the advertised product. These features need not be deceptive to affect behaviour. They can change what people notice and how much time they spend considering alternatives.",
      "Suppose that a household wants to compare the cost of delivery with shopping in person. Looking only at the delivery charge would provide an incomplete picture. A fair comparison would include the prices of the same products, additional service charges, transport costs, and purchases made to reach a minimum order. It would also acknowledge the value of time saved, although assigning a precise monetary value to that time may be difficult. Keeping receipts for several ordinary weeks would be more informative than comparing a single promotional order with an unusually expensive visit to a shop.",
      "There are consequences beyond the household budget. Consolidating several deliveries into one route may be more efficient than separate journeys, but the environmental outcome depends on factors such as transport methods, distance, packaging and order frequency. A customer who orders one small item at a time may create different demands from someone who schedules a single weekly delivery. It would therefore be misleading to claim that delivery is always environmentally preferable or always worse. The relevant comparison depends on what would have happened without the service.",
      "Consumers can preserve the advantages of convenient services by establishing a few deliberate habits. They might decide on a regular ordering day, turn off unnecessary promotional notifications and review the total cost before paying. Businesses, meanwhile, can make it easier for customers to understand charges by displaying the full price early in the process. Such measures do not require rejecting technology. They recognise that reducing friction in a transaction is beneficial only when the transaction itself serves a worthwhile purpose. A service that makes a useful activity easier deserves a different evaluation from one that simply makes unnecessary activity easier to repeat.",
      "A further complication concerns the distinction between the initial adoption of a convenient service and its continued use. When someone first begins using a delivery application, the decision may involve a careful assessment of price, reliability and available alternatives. After several months, however, placing an order may have become an ordinary part of the household routine. The customer may no longer reconsider the original decision each time a purchase is made. This is not necessarily undesirable: routines reduce the effort involved in recurring decisions. Nevertheless, an arrangement that was appropriate when it was introduced may become less suitable if the household's circumstances or the service's conditions change.",
      "Consider a family that began ordering groceries while a member of the household was recovering from an injury. The initial decision was clearly practical. The family could obtain essential supplies without creating additional pressure on the person providing care. Once the injury had healed, however, the family continued to use the service. Its members might still find delivery worthwhile, but the original reason no longer provides a complete justification. They could review whether their new routine remains convenient, how much it costs and whether some purchases could be combined with journeys they already make. The point is not that habits must always be abandoned when circumstances change, but that their continuing value should occasionally be considered.",
      "Businesses have legitimate reasons to encourage repeat purchases. Predictable demand can help a delivery service organise staffing, purchase supplies and make efficient use of its vehicles. A subscription that reduces the cost of regular orders may offer real savings to customers who already use the service frequently. Yet the incentives created by a subscription may affect consumers differently. Someone who has paid for unlimited deliveries may feel that ordering frequently is the best way to obtain value from the subscription. In doing so, the customer may increase spending on products even though the cost of each delivery appears to have fallen. Evaluating a subscription therefore requires looking beyond the individual transaction and considering the overall pattern of use.",
      "It is also worth distinguishing the amount of time saved from what happens to that time. A person who avoids an unnecessary journey may be able to rest, spend time with family or complete another important task. Those benefits can be substantial even when they are difficult to express in financial terms. On the other hand, a service that appears to save time may introduce different tasks, such as comparing products on a small screen, monitoring delivery updates or arranging for someone to be available when an order arrives. Whether the service genuinely reduces the demands on the customer depends partly on how well these new tasks fit into the person's life.",
      "Imagine that a customer compares two delivery services. The first has a lower advertised charge but provides only a broad estimate of the arrival time. The second is slightly more expensive but offers a narrower delivery window that allows the customer to organise the rest of the day. A purely financial comparison might favour the first option. A customer who needs to attend several appointments, however, may consider the more predictable service better value. This example illustrates why the cheapest advertised price is not always the most useful measure of affordability. Uncertainty and inconvenience can have real consequences, although their importance varies from person to person.",
      "The same reasoning applies to the way services present information. A customer who receives a detailed estimate before placing an order can compare options more effectively than someone who discovers additional charges near the end of the process. Displaying the total price early may reduce the likelihood of unexpected expenditure and make competition between providers more meaningful. A service can also offer a straightforward way to review previous orders, rather than presenting only the amount saved through individual promotions. A record showing total monthly spending would help some customers identify whether their purchasing habits had changed. Transparency in this context is not merely about making information available somewhere; it is about presenting relevant information when a decision can still be changed.",
      "There is a danger, however, in assuming that every consumer has the same ability to analyse these choices. Some households have limited access to transport, shops or reliable internet connections. Others may have little spare time to compare several services before obtaining essential supplies. An elaborate set of cost calculations might be helpful to someone who has the resources to consider alternatives but less useful to a person facing immediate practical difficulties. Consumer advice should recognise these limitations. It can encourage informed decisions without suggesting that people who rely on convenient services have necessarily made poor choices.",
      "Public institutions and businesses can also contribute to making alternatives realistic. If a neighbourhood has few accessible shops, telling residents to avoid delivery charges may not address the underlying problem. Improving access to local services could change the choices available to residents. Similarly, clear delivery arrangements can make online shopping a more reliable option for people who need additional support. The value of convenience is partly shaped by the quality of the alternatives. A service that seems unnecessary in one environment may provide an important practical benefit in another.",
      "A household that wants to understand its own purchasing habits could conduct a small experiment. For several weeks, it could record the types of orders placed, the total expenditure and the reasons for using delivery. It could note which orders were planned and which were made in response to a promotion or a missing item. The aim would not be to classify every purchase as good or bad. Rather, it would be to identify recurring patterns and decide whether a different routine would better serve the household's needs. The results might reveal that most deliveries were useful, that a few unnecessary orders created substantial additional expense or that a subscription was no longer appropriate.",
      "Such an experiment would have limitations. A few weeks might not capture seasonal changes, unusually busy periods or emergencies. The household could nevertheless obtain enough information to reconsider a routine that had previously been accepted without much thought. It might decide to retain the service while placing fewer small orders, or to use delivery only when the practical advantages were particularly clear. Another household could reach the opposite conclusion and choose to use the service more often because it genuinely reduced pressure on family members. Different decisions can be reasonable when they respond to different circumstances. The larger lesson is that convenience is a means of supporting worthwhile activities, not an objective that should automatically override every other consideration."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What is the author’s central argument?",
        "options": [
          "Delivery services should be avoided by everyone.",
          "Convenience always reduces household costs.",
          "Convenient services should be used with awareness of trade-offs."
        ],
        "answer": 2,
        "evidence": "The issue is whether users understand the trade-offs they are making."
      },
      {
        "type": "choice",
        "prompt": "Why does the author mention people with limited mobility?",
        "options": [
          "To argue that shops should close",
          "To acknowledge a genuine benefit of delivery",
          "To suggest they spend more money"
        ],
        "answer": 1,
        "evidence": "Delivery can improve access for people who have limited mobility."
      },
      {
        "type": "choice",
        "prompt": "What comparison does the author recommend?",
        "options": [
          "Total delivery cost versus an ordinary shop",
          "Delivery fees between two apps only",
          "Packaging colour between shops"
        ],
        "answer": 0,
        "evidence": "Comparing the total cost with an ordinary shop is more informative."
      },
      {
        "type": "true_false",
        "prompt": "The author recommends checking receipts and setting a budget.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Planning orders, checking receipts and setting a budget may allow them to enjoy the advantages."
      },
      {
        "type": "true_false",
        "prompt": "The author claims delivery services are inherently harmful.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "The service itself is not necessarily the problem."
      },
      {
        "type": "choice",
        "prompt": "Why might the two households experience different benefits?",
        "options": [
          "Their routines and transport needs differ",
          "They order from different companies",
          "Only one receives food"
        ],
        "answer": 0,
        "evidence": "Both households benefit from convenience, but the effect on their routines and budgets may be quite different."
      },
      {
        "type": "choice",
        "prompt": "Which comparison would give a fuller picture of delivery costs?",
        "options": [
          "Only the first promotional offer",
          "Only the advertised charge",
          "Equivalent products and all related costs"
        ],
        "answer": 2,
        "evidence": "A fair comparison would include the prices of the same products, additional service charges, transport costs, and purchases made to reach a minimum order."
      },
      {
        "type": "choice",
        "prompt": "Why can an unlimited-delivery subscription lead to higher overall expenditure?",
        "options": [
          "A customer may place more orders to make use of it",
          "It necessarily raises the advertised delivery fee",
          "It prevents people from reviewing receipts"
        ],
        "answer": 0,
        "evidence": "Someone who has paid for unlimited deliveries may feel that ordering frequently is the best way to obtain value from the subscription. In doing so, the customer may increase spending on products even though the cost of each delivery appears to have fallen."
      },
      {
        "type": "true_false",
        "prompt": "A suggested list can be useful when it reminds customers of things they regularly need.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "A suggested shopping list can be helpful when it reminds a customer to purchase something they regularly need."
      },
      {
        "type": "true_false",
        "prompt": "A short household spending experiment necessarily captures seasonal changes.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "A few weeks might not capture seasonal changes, unusually busy periods or emergencies."
      }
    ]
  },
  {
    "id": "b2-02",
    "level": "B2",
    "title": "When silence is useful",
    "titleUk": "Коли тиша корисна",
    "paragraphs": [
      "In many workplaces, a successful meeting is assumed to be one in which everyone contributes immediately. A long pause after a question may make a chairperson uncomfortable, prompting them to rephrase the question or answer it themselves. Yet silence does not necessarily indicate a lack of ideas. Some people need time to organise their thoughts, especially when discussing a complicated issue in a language they did not grow up speaking.",
      "One team experimented with sending discussion questions in advance and allowing two minutes of quiet writing before each major decision. Initially, participants found the approach slightly awkward. Over time, however, the range of suggestions increased because employees who rarely interrupted others had an opportunity to prepare their contributions. The change did not eliminate disagreement, nor was that its purpose. It simply made disagreement more informed.",
      "There are situations in which rapid responses remain essential, particularly when a decision is urgent. The lesson is not that every conversation should become slower, but that speed should not be mistaken for quality. A well-timed pause can make a discussion more inclusive without making it less productive.",
      "The assumption that effective communication must be immediate is especially visible in meetings where participants have different professional roles. Someone familiar with the subject may be able to respond to a technical question without hesitation, whereas another participant may need to consider how the proposed decision would affect a different department. A rapid contribution is not necessarily superficial, and a delayed contribution is not necessarily thoughtful. The problem arises when speed becomes an informal measure of competence before the content of a person's response has been considered.",
      "One reason this assumption persists is that meetings have limited time. A chairperson is expected to maintain momentum, and a period of silence can appear to threaten the schedule. There may also be uncertainty about whether participants have understood the question. In some cases, repeating or clarifying it is entirely appropriate. However, answering the question on behalf of the group can unintentionally narrow the discussion. Once a senior participant has suggested a preferred solution, others may find it more difficult to express a different view.",
      "The team's experiment with advance questions attempted to separate the process of forming an opinion from the process of presenting it. Participants received a brief description of the decision and the main issues to consider. At the meeting, the chairperson introduced the topic without immediately recommending a solution. During the quiet writing period, people made private notes. Afterwards, the group invited contributions from different participants before discussing which proposals were feasible. Nobody was required to read out every note they had made.",
      "The experiment had limitations. Preparing questions in advance took additional effort, and not every decision could be predicted. Some participants preferred to develop their ideas through conversation rather than individual writing. The team therefore used the method selectively, particularly for decisions where several perspectives were important. Routine updates continued to be handled quickly. The aim was not to introduce a rigid procedure into every discussion but to create a more suitable process for particular kinds of decisions.",
      "Evaluating the experiment also required care. An increase in the number of suggestions did not automatically prove that the decisions were better. Some suggestions might be impractical or overlap with one another. More useful questions included whether important risks were being identified earlier, whether participants understood the reasons for final decisions, and whether people with relevant knowledge had opportunities to contribute. The team could observe these outcomes and adjust the process accordingly, rather than assume that a longer meeting was inherently more productive.",
      "There is a broader lesson for communication outside the workplace. In a classroom, an immediate answer may come from the student who is most comfortable speaking, while other students are still considering the question. In a conversation between friends, a pause may indicate that someone is trying to respond carefully to a difficult subject. Yet silence can also signal confusion or discomfort, so it should not be interpreted automatically as a positive sign. The most useful response is often to create a reasonable opportunity for participation and then check what people need. A well-managed conversation balances the practical value of time with the value of hearing contributions that might otherwise remain unspoken.",
      "One difficulty in evaluating pauses is that their meaning depends heavily on the relationship between the participants. In a familiar team where people feel comfortable acknowledging uncertainty, a period of silence after a question may simply indicate that the issue deserves consideration. In a less trusting environment, the same silence may arise because employees are reluctant to disagree with someone who has greater authority. Introducing a quiet writing period might help in both situations, but it would not address every underlying problem. If participants believe that expressing a concern will have negative consequences, providing additional time to formulate the concern may not make them more willing to share it.",
      "This distinction has implications for the role of the chairperson. A meeting leader can make it clear that different perspectives are welcome, but participants will also observe how that statement is put into practice. If objections are repeatedly dismissed without examination, employees may reasonably conclude that disagreement is not genuinely encouraged. Conversely, a leader who asks someone to explain a concern and considers its implications demonstrates that participation can influence the discussion. The formal structure of a meeting matters, but the behaviour of the people responsible for decisions can be equally important in determining whether useful information is shared.",
      "Suppose that a team is considering a change to the way it handles customer requests. A member of the technical department proposes an approach that would reduce the time needed to process each request. Employees who deal directly with customers may recognise that the proposal could create difficulties for people whose requests do not fit standard categories. They might need a few minutes to identify examples and explain why those cases matter. If the team reaches a decision immediately after hearing the technical proposal, it may overlook knowledge that was available within the group but had not yet been expressed. A short period of reflection would not guarantee a better decision, but it could create an opportunity for the relevant information to enter the discussion.",
      "The reverse situation is also possible. A group might spend a long time considering a routine matter even though the necessary information is already available and everyone agrees about the appropriate response. Requiring extensive individual preparation in such cases would create unnecessary work. The cost of a slower process should therefore be assessed in relation to the complexity and importance of the decision. A meeting concerned with a long-term change that will affect several departments may justify additional preparation. A straightforward update about an existing arrangement may not. Effective communication involves choosing a suitable level of attention rather than consistently favouring either speed or deliberation.",
      "Another consideration is that written preparation may be more accessible to some participants than to others. A person who expresses ideas confidently in writing may find it helpful to make notes before speaking. Someone who finds writing difficult may prefer to consider the question through conversation or by using a diagram. If a team treats written notes as a compulsory demonstration of preparation, it could create a different form of exclusion while attempting to address the original problem. The opportunity to reflect should not be confused with a requirement that everyone reflect in exactly the same way. Participants can be offered alternative methods of organising their thoughts when these are appropriate to the situation.",
      "The design of the advance question also affects the quality of the resulting discussion. A question that asks participants to approve or reject a specific proposal may lead them to focus mainly on its immediate advantages and disadvantages. A broader question about the problem the proposal is intended to solve may reveal additional possibilities. For example, asking how to reduce waiting times might encourage a wider range of suggestions than asking whether a particular scheduling system should be introduced. The first formulation invites participants to consider the objective, while the second starts from one possible means of achieving it. Both kinds of question have a place, but they serve different purposes.",
      "When the team reviewed its experiment after several months, it considered whether the changes were helping people communicate more effectively outside meetings as well. Some employees had begun sending short explanations of complex issues before requesting a decision. Others found that making a few notes in advance helped them explain a concern more clearly in an ordinary conversation. The group did not attempt to turn these habits into formal requirements for every interaction. Instead, it recognised them as useful techniques that people could choose when they needed more time to think or wanted to reduce the risk of being misunderstood.",
      "Measuring improvement remained difficult. The team could record how long meetings lasted and how many people contributed, but these figures would not reveal whether the discussion had addressed the most important issues. A meeting with many contributions might still avoid an uncomfortable subject. A shorter meeting with only a few speakers could be effective if those speakers had the necessary information and other participants had already been consulted. The team therefore examined examples of decisions that had subsequently needed revision. It asked whether information that became important later could reasonably have been identified during the original discussion. Such a review could help identify weaknesses in the process without assuming that every unexpected development indicated a failure.",
      "Outside professional settings, the ability to tolerate a pause can also be valuable in learning. A teacher who asks a challenging question may be tempted to respond as soon as the first student raises a hand. Allowing a little more time can enable other learners to formulate their own answers rather than simply listen to the quickest response. However, the teacher still needs to observe whether students understand the task and whether additional explanation would help. Silence should not be used as an excuse to leave learners confused. It is useful when it creates a space for active thought, not when it replaces the support that participants require.",
      "Ultimately, a well-designed discussion distinguishes the process of generating ideas, the process of evaluating them and the process of making a decision. These activities do not always need to happen separately, but separating them occasionally can help a group notice when one is being neglected. A meeting may generate many suggestions without evaluating them carefully, or reach a decision before the relevant ideas have been identified. A pause is one possible tool for improving this balance. Its value depends on the nature of the task, the needs of the participants and the willingness of decision-makers to consider what people contribute. The objective is not silence itself. It is communication that uses time and attention in ways that make the resulting decisions more informed."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What does the author challenge?",
        "options": [
          "The use of written questions altogether",
          "The assumption that immediate contributions indicate a good meeting",
          "The idea that workplace decisions need discussion"
        ],
        "answer": 1,
        "evidence": "Speed should not be mistaken for quality."
      },
      {
        "type": "true_false",
        "prompt": "The experiment was intended to eliminate disagreement.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "The change did not eliminate disagreement, nor was that its purpose."
      },
      {
        "type": "choice",
        "prompt": "Why did suggestions become more varied?",
        "options": [
          "Quieter employees had time to prepare.",
          "Disagreement was prohibited.",
          "The team reduced the number of participants."
        ],
        "answer": 0,
        "evidence": "Employees who rarely interrupted others had an opportunity to prepare their contributions."
      },
      {
        "type": "choice",
        "prompt": "What does the final paragraph imply?",
        "options": [
          "Every decision should include a long delay.",
          "Quick responses have no value.",
          "The best pace depends on the situation."
        ],
        "answer": 2,
        "evidence": "There are situations in which rapid responses remain essential."
      },
      {
        "type": "true_false",
        "prompt": "Participants initially found the change awkward.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Initially, participants found the approach slightly awkward."
      },
      {
        "type": "choice",
        "prompt": "Why might an early suggestion from a senior participant narrow a discussion?",
        "options": [
          "It increases the number of written notes",
          "It makes the meeting shorter automatically",
          "Others may hesitate to present a different view"
        ],
        "answer": 2,
        "evidence": "Once a senior participant has suggested a preferred solution, others may find it more difficult to express a different view."
      },
      {
        "type": "choice",
        "prompt": "How did the team use quiet writing after the experiment?",
        "options": [
          "For every conversation without exception",
          "Selectively for suitable decisions",
          "Only for urgent routine updates"
        ],
        "answer": 1,
        "evidence": "The team therefore used the method selectively, particularly for decisions where several perspectives were important."
      },
      {
        "type": "choice",
        "prompt": "Why might a requirement to make written notes create another kind of exclusion?",
        "options": [
          "It guarantees that every contribution is shallow",
          "It removes all time for participants to think",
          "Some people organise their thoughts better through other methods"
        ],
        "answer": 2,
        "evidence": "Someone who finds writing difficult may prefer to consider the question through conversation or by using a diagram."
      },
      {
        "type": "true_false",
        "prompt": "Participants were allowed to make private notes.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "During the quiet writing period, people made private notes."
      },
      {
        "type": "true_false",
        "prompt": "The passage claims that a quiet writing period will resolve every underlying problem of trust.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Introducing a quiet writing period might help in both situations, but it would not address every underlying problem."
      }
    ]
  },
  {
    "id": "b2-03",
    "level": "B2",
    "title": "Designing for attention",
    "titleUk": "Дизайн і увага",
    "paragraphs": [
      "Educational platforms often reward learners for maintaining a daily streak. The idea is straightforward: regular practice can help make a difficult activity feel manageable. A visible record of consecutive days may encourage learners to return even when their initial enthusiasm has faded. However, the same feature can become counterproductive if preserving the streak matters more than understanding the material.",
      "Consider a learner who completes the easiest available exercise every evening solely to avoid losing a record. The platform may register consistent activity, yet the learner might rarely encounter material that challenges them. Conversely, someone who takes a day off to rest and returns to more demanding exercises may be making meaningful progress, even though the visible record looks less impressive.",
      "A thoughtful learning platform therefore needs to distinguish engagement from mastery. Streaks can remain useful as reminders, but they should be accompanied by indicators that reflect understanding, such as performance on unfamiliar tasks and the ability to recall material after a delay. No single metric captures every aspect of learning. Combining several carefully chosen measures helps prevent a useful motivational tool from becoming the goal itself.",
      "Consider a platform that reports two learners' activity over the course of a month. One has completed a short vocabulary exercise every day, correctly answering questions about familiar words. The other has studied on fewer days but has practised reading unfamiliar passages, revisited earlier mistakes and attempted more demanding writing tasks. A simple activity counter will make the first learner appear more successful. Yet without information about the difficulty of the exercises, the retention of knowledge and the learners' starting points, that conclusion would be premature.",
      "Metrics are attractive because they reduce complicated activities to information that can be displayed clearly. A learner can easily understand that a streak has reached thirty days, whereas progress in expressing an argument in a foreign language is more difficult to represent. The simplicity of a streak is part of its appeal. It provides a visible reminder of regular effort, which can be encouraging during the early stages of developing a habit. Problems emerge when this easily measured activity is treated as a complete description of learning.",
      "The design of a reward can alter the behaviour it is supposed to measure. If maintaining a streak requires completing any exercise, a learner who is short of time has an incentive to select the easiest available task. This may be a reasonable choice on an unusually busy day. However, when the same strategy is used repeatedly, the reward no longer provides much evidence of progress. The platform records participation, but the learner may be avoiding the very material that would help develop their skills.",
      "A more balanced approach would combine activity information with evidence of understanding. For example, vocabulary progress might include the ability to recall a word after several days without seeing its translation. Reading progress might include answering questions about a new passage rather than recognising answers from a familiar exercise. A writing task might be assessed against clear criteria that describe how effectively the learner communicates an idea. These measures address different skills, and none should be mistaken for a complete assessment of language ability.",
      "Designers should also consider how feedback affects motivation. Showing learners a long list of weaknesses without acknowledging their improvements may be discouraging. Conversely, awarding positive messages for every action can make feedback less informative. A useful progress display might distinguish between material that has been introduced, material that can be recognised and material that can be recalled independently. It could then recommend a manageable next step without suggesting that a learner has failed simply because they have taken a day off.",
      "Finally, the platform's objectives should be made explicit. An organisation may value frequent visits because they demonstrate continued engagement with a product. A learner may value the ability to communicate more confidently outside the platform. These goals can support each other, but they are not identical. When designers choose what to reward, they should examine whether the chosen behaviour is likely to contribute to the learner's objective. A streak can remain an enjoyable part of the experience. It becomes a stronger educational tool when it encourages sustained practice without obscuring the more important question of what the learner is actually learning.",
      "An additional challenge for educational platforms is that learners differ substantially in their reasons for studying. A student preparing for an examination may need to master particular topics by a specific date, while someone learning a language for travel might prioritise everyday conversations. Another learner may simply enjoy reading in a foreign language and have no immediate interest in formal assessment. A uniform activity target can provide a convenient starting point, but it may not reflect these different objectives. Two people who complete the same number of exercises could be making very different kinds of progress towards the goals that matter to them.",
      "Consider a learner who has decided to improve reading comprehension. A platform could encourage this learner to read a short passage each day and answer questions about it. If the passages repeatedly use familiar vocabulary and simple structures, the learner may obtain high scores while encountering relatively few new challenges. The activity may still be useful for maintaining confidence, particularly after a break. However, if the objective is to understand increasingly complex texts, the system needs to provide opportunities to practise dealing with unfamiliar expressions, identifying the main argument and distinguishing important details from examples. A high score on easy material cannot by itself demonstrate improvement in these more demanding skills.",
      "Difficulty is not the only factor that influences the value of an exercise. The way the questions are presented can affect what the learner is required to remember or understand. For example, selecting a translation from several visible options involves a different task from producing the translation without seeing it. Both activities may have a useful role at different stages of learning. Recognition can help introduce unfamiliar vocabulary, while independent recall can reveal whether the learner is able to retrieve a word without immediate support. A platform that treats correct answers in both formats as identical evidence may fail to communicate these differences. It could instead explain which type of knowledge each activity is intended to develop.",
      "Designers also need to consider what happens when a learner makes a mistake. Immediate feedback can provide useful information, but the learner may simply recognise the corrected answer and move on. A later exercise that requires the same knowledge in a different context can help determine whether the correction has been understood. If the platform records a topic as mastered immediately after the learner has seen the correct answer, it may overestimate what the learner can do independently. A more informative system would allow knowledge to be reviewed after a delay and use the result to guide future practice. This need not involve complicated scores; even a clear indication that a word or concept should be revisited can be helpful.",
      "Suppose that two learners make the same number of mistakes during a practice session. One is working on material that has just been introduced, while the other is reviewing material that they have successfully practised several times. The meaning of the mistakes may differ. In the first situation, errors may be an expected part of becoming familiar with a new topic. In the second, they may indicate that knowledge has not been retained as well as expected. Presenting both learners with the same negative message would provide little guidance. Feedback that identifies the stage of learning can help them understand what kind of practice is appropriate next.",
      "There is also a relationship between the design of goals and the amount of control learners feel they have. A daily target that is too demanding may become discouraging when a learner has other responsibilities. A target that is too easy may provide little direction after the learner has developed a stable routine. Allowing people to adjust their goals can make them more relevant to their circumstances, provided that changes are presented as part of planning rather than as a way to avoid every difficult task. A learner might choose a short review on a particularly busy day and set aside more time for demanding work later in the week. The important question is whether the overall pattern continues to support meaningful learning.",
      "From the perspective of the organisation operating a platform, activity metrics have practical value. They can reveal whether learners return, which parts of the service they use and where they tend to stop. Such information may help identify confusing interfaces or activities that are difficult to access. However, the same metrics can be misleading if they are used without considering why a person has stopped. A learner may leave because an exercise is frustrating, because they have achieved their immediate objective or because they have chosen another way to practise. The absence of activity does not automatically establish that the platform has failed to support learning. Additional information may be necessary to interpret the pattern.",
      "Similarly, an increase in time spent on a platform is not inherently a positive educational outcome. If a revised interface allows learners to find suitable material more quickly, the time required to complete a useful study session may decrease. A system that rewards users for remaining on the site for as long as possible might therefore create an incentive that conflicts with the objective of making learning efficient. Designers should be cautious about assuming that engagement measures always move in the same direction as educational outcomes. A useful platform might help learners achieve more in less time or encourage them to practise skills in settings outside the application.",
      "One possible approach is to provide different kinds of progress information without combining them into a single ranking. An activity record can show how regularly a person has practised, while separate indicators describe performance in particular skills. A vocabulary section might distinguish words that have been introduced from words that have been recalled successfully on more than one occasion. A reading section could show the difficulty of passages completed and the types of questions answered accurately. The learner would then have a more detailed picture of strengths and areas for improvement. Such a display should remain understandable; too many unexplained indicators could create a different problem by making it difficult to decide what to do next.",
      "The platform should also avoid creating an impression of precision that its assessments cannot support. Completing a collection of exercises does not necessarily establish that a learner has reached a particular level across every aspect of language use. An assessment that focuses mainly on reading and vocabulary cannot provide complete evidence about speaking or listening. Clear explanations of what has been measured can make progress information more trustworthy. Learners can use the results to guide their practice without assuming that every number describes a general ability with perfect accuracy.",
      "The central design principle is that incentives, measurements and educational objectives should be aligned as far as possible. A streak can encourage regular participation, a challenging exercise can reveal gaps in understanding, and a later review can provide evidence of retention. Each serves a different purpose. Their combination can support a learner more effectively than a system that attempts to make one visible number represent everything. The most useful question for a platform is not simply whether people have returned today, but whether the activities they have chosen are helping them develop the knowledge and skills they set out to acquire."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What potential weakness of streaks is described?",
        "options": [
          "Learners may prioritise keeping the streak over understanding.",
          "Streaks prevent learners from practising regularly.",
          "Streaks always measure long-term recall accurately."
        ],
        "answer": 0,
        "evidence": "Preserving the streak matters more than understanding the material."
      },
      {
        "type": "choice",
        "prompt": "Why does the author compare two learners?",
        "options": [
          "To show that rest is always better than study",
          "To prove easy exercises are never useful",
          "To distinguish visible activity from meaningful progress"
        ],
        "answer": 2,
        "evidence": "The learner may register consistent activity yet rarely encounter challenging material."
      },
      {
        "type": "choice",
        "prompt": "What does the author recommend?",
        "options": [
          "Using only the number of consecutive days",
          "Combining engagement measures with indicators of understanding",
          "Removing every motivational feature"
        ],
        "answer": 1,
        "evidence": "Streaks should be accompanied by indicators that reflect understanding."
      },
      {
        "type": "true_false",
        "prompt": "The author recognises that streaks can encourage regular practice.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "A visible record of consecutive days may encourage learners to return."
      },
      {
        "type": "true_false",
        "prompt": "The author argues one metric captures all aspects of learning.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "No single metric captures every aspect of learning."
      },
      {
        "type": "choice",
        "prompt": "Why is the streak alone insufficient for comparing learners?",
        "options": [
          "It cannot count days",
          "It omits task difficulty and retention",
          "It measures exactly how well they speak"
        ],
        "answer": 1,
        "evidence": "Without information about the difficulty of the exercises, the retention of knowledge and the learners' starting points, that conclusion would be premature."
      },
      {
        "type": "choice",
        "prompt": "Which vocabulary measure offers evidence beyond activity?",
        "options": [
          "Independent recall after a delay",
          "The number of notifications received",
          "The number of opened pages"
        ],
        "answer": 0,
        "evidence": "Vocabulary progress might include the ability to recall a word after several days without seeing its translation."
      },
      {
        "type": "choice",
        "prompt": "Why could a more efficient learning interface reduce time spent on a platform?",
        "options": [
          "Correct answers could no longer be recorded",
          "Learners might locate suitable material more quickly",
          "Learning would necessarily become less effective"
        ],
        "answer": 1,
        "evidence": "If a revised interface allows learners to find suitable material more quickly, the time required to complete a useful study session may decrease."
      },
      {
        "type": "true_false",
        "prompt": "The learner's objective and the organisation's engagement objective may differ.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "These goals can support each other, but they are not identical."
      },
      {
        "type": "true_false",
        "prompt": "A reading and vocabulary assessment provides complete evidence of speaking and listening ability.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "An assessment that focuses mainly on reading and vocabulary cannot provide complete evidence about speaking or listening."
      }
    ]
  },
  {
    "id": "b2-04",
    "level": "B2",
    "title": "A second life for public spaces",
    "titleUk": "Друге життя громадських просторів",
    "paragraphs": [
      "A city council proposed converting an underused car park into a temporary public square. Supporters argued that the neighbourhood lacked places where residents could spend time without purchasing anything. Some shop owners, meanwhile, feared that removing parking spaces would discourage customers. Rather than committing to an expensive permanent redesign, the council introduced a three-month trial with movable seating, plants and a small area for community events.",
      "The trial produced mixed results. The square attracted families and workers during lunch breaks, and several nearby cafés reported increased sales. Other businesses saw little change, and residents complained that deliveries had become less convenient. The council collected feedback and adjusted the layout to allow deliveries during certain hours. It also extended the trial to observe how the space would be used in colder weather.",
      "The example illustrates the advantage of reversible decisions. Temporary changes can reveal consequences that forecasts might miss, while allowing authorities to respond before investing in permanent construction. Such trials are not a substitute for consultation, but they can make consultation more concrete by giving residents an actual experience to discuss.",
      "Before the trial began, the car park had a relatively low level of use during much of the day, although it became busier on certain evenings. Supporters of the square saw an opportunity to create a place where residents could meet without needing to pay for access. Opponents were concerned that averages might conceal periods when parking was particularly valuable. A business receiving deliveries early in the morning, for example, had different requirements from a café whose customers arrived on foot during the afternoon.",
      "These concerns demonstrated the difficulty of evaluating a public space through a single measure. Counting parking spaces would describe one function of the area but say little about the value of providing seating or allowing community events. Counting visitors to the new square would provide evidence of its popularity but would not necessarily show how neighbouring streets were affected. The council needed to consider how the proposal distributed benefits and inconvenience among people who used the area in different ways.",
      "The temporary design was intended to make adjustment possible. Seating could be moved, plants were placed in containers, and the space allocated to activities could be changed according to demand. The council published information about the trial and invited comments from residents and businesses. It also recorded observations at different times of day rather than relying entirely on comments from the most frequent visitors. Although the design was temporary, the organisers still had to consider accessibility, safe movement through the area and arrangements for maintenance.",
      "During the first weeks, the square was often busy when the weather was pleasant. Some residents brought their own lunches and sat outside, while others purchased food from nearby businesses. Families used the seating during the afternoon. The organisers also noticed that the area was relatively quiet on certain mornings. This raised the question of whether some of the space could serve a different function during those periods without undermining the purpose of the square. Delivery access was one of the issues that could potentially be addressed through a revised schedule.",
      "Feedback was not always consistent. A nearby shop owner who reported an increase in customers might attribute it to the new space, although seasonal changes or other factors could also have contributed. Similarly, a decline in sales would not automatically establish that the trial was responsible. The council could compare observations with earlier periods and examine how people travelled to the area, but it would still need to recognise the limits of the available evidence. A temporary experiment can improve understanding without producing perfect information.",
      "Extending the trial into colder weather was therefore a meaningful decision. A square that worked well during summer might require different seating, shelter or programming during winter. The extra observations would help the council determine whether the space could offer year-round benefits and what changes would be necessary. The broader advantage of reversible decisions is that they create room for learning before resources are committed permanently. However, a trial must have clear evaluation criteria and an honest process for responding to its results. Otherwise, describing a proposal as temporary may simply delay an unresolved disagreement rather than help residents reach a better decision.",
      "A particularly important issue in evaluating the trial was identifying the groups whose experiences might not be represented by visible activity in the square. People who enjoyed the new seating could be observed using it, and businesses could provide information about their own customers. Other residents, however, might avoid the area because they found it difficult to reach or because changes to the surrounding streets affected their journeys. If the council relied mainly on feedback collected inside the square, it might receive a disproportionately positive account of the trial. Understanding who is absent can be as important as understanding who is present when assessing a public space.",
      "The council could address this problem by collecting information in different ways. It might invite comments from people who live in nearby streets, speak to organisations representing residents with mobility difficulties and ask businesses about the times when access is particularly important. It could also provide opportunities to submit feedback without attending a public meeting. None of these methods would guarantee that every perspective was represented, but using several approaches could reduce the risk of basing a decision entirely on the experiences of the most visible or vocal groups. The purpose would be to identify significant practical concerns rather than simply count expressions of support and opposition.",
      "The council also needed to distinguish between temporary inconvenience caused by the introduction of the trial and difficulties that were likely to continue if the square became permanent. During the first few days, visitors might be uncertain about where to walk or where deliveries were permitted because they had not yet become familiar with the new arrangement. Clear signs and better communication could address some of these problems. Other difficulties, such as a lack of suitable access to a building, might require changes to the physical layout. Treating all complaints as evidence that the entire idea had failed would overlook the possibility of improvement. At the same time, dismissing every complaint as a temporary adjustment would prevent the council from identifying problems that deserved a more substantial response.",
      "The design of the trial made it possible to test several arrangements without committing to permanent construction. For instance, moving a group of seats could create a wider route through the square, while changing the time of an activity might reduce conflict with deliveries. The council could observe the consequences of such adjustments and ask the people affected whether the new arrangements worked better. This process would be more useful if the changes were recorded clearly. Otherwise, it might be difficult to determine which version of the layout had produced a particular result. Maintaining a simple record of decisions would also make the evaluation more transparent to residents who wanted to understand how their comments had influenced the trial.",
      "There was a financial dimension as well. Temporary furniture and plants required an initial investment, and the square needed maintenance throughout the trial. A permanent redesign might involve additional expenditure on construction, drainage, lighting and other facilities. The council would need to consider whether the expected benefits justified these costs and whether the resources could be used more effectively elsewhere. However, the value of a public space cannot necessarily be measured through direct income alone. A place that allows people to rest, meet friends or participate in free activities may provide benefits that do not appear in a simple financial report. A reasonable assessment would acknowledge both the cost of providing the space and the different forms of value it might create.",
      "One possible criticism of a trial is that a temporary space may attract attention simply because it is new. Residents who visit during the first few weeks might do so out of curiosity rather than because the square meets a continuing need. If the initial popularity declines, the council would need to investigate why. The decline might reflect the end of the initial excitement, a change in the weather or problems with the way activities are organised. Observing the space over a longer period could provide more useful information about ordinary patterns of use. It could also show whether some groups become more comfortable using the space after they have had time to understand what is available.",
      "The opposite effect is possible too. A new public space may initially attract relatively few visitors because residents do not know that it exists or are uncertain about what they are allowed to do there. Some people may assume that seating belongs to a nearby café and that they must purchase something before using it. Clear information could make the purpose of the square more obvious. As residents become familiar with the space, its use might increase. An evaluation conducted immediately after opening would not necessarily reveal this longer-term pattern. This is one reason why the council's decision to extend the trial could be more informative than a judgment based entirely on the first month.",
      "A reversible decision also creates a responsibility to explain what will happen after the experiment. Residents may support a temporary arrangement because they believe that their feedback will influence the final decision. If the council has already made an irreversible commitment while describing the project as a trial, that confidence may be undermined. The evaluation should therefore identify the criteria that will be considered before a permanent decision is made. These might include accessibility, demand for the space, effects on neighbouring businesses, maintenance costs and the feasibility of accommodating deliveries. It would be useful to explain how conflicts between these criteria will be considered rather than promise that every requirement can be satisfied completely.",
      "The lessons of the trial could also be applied to other neighbourhoods, although the same design would not necessarily work everywhere. An area with a different mix of businesses, residents and transport options might require a different arrangement. A successful square in one location would provide evidence that a particular approach can work under certain conditions, not proof that every underused car park should be converted. The council could use what it had learned about consultation, temporary design and evaluation while still examining the specific needs of each new location.",
      "In this way, the value of the experiment extends beyond the decision about one piece of land. It demonstrates a method of dealing with uncertainty that combines action with observation. Rather than waiting until every disagreement has been resolved in theory, a public authority can sometimes test a limited proposal and learn from its consequences. The method works best when changes remain genuinely reversible, affected people can contribute to the evaluation and the authority is willing to modify or abandon an arrangement if important problems cannot be addressed. A successful trial does not necessarily lead to the proposal that was originally imagined. It can lead to a revised decision that reflects a better understanding of the people and circumstances involved."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "Why was the redesign temporary?",
        "options": [
          "To avoid receiving any public feedback",
          "To guarantee that shops would gain customers",
          "To learn from real use before committing permanently"
        ],
        "answer": 2,
        "evidence": "Temporary changes can reveal consequences that forecasts might miss."
      },
      {
        "type": "choice",
        "prompt": "What problem emerged during the trial?",
        "options": [
          "All cafés reported falling sales.",
          "Deliveries became less convenient.",
          "Nobody visited the square."
        ],
        "answer": 1,
        "evidence": "Residents complained that deliveries had become less convenient."
      },
      {
        "type": "choice",
        "prompt": "How does the author view trials and consultation?",
        "options": [
          "Trials complement consultation.",
          "Trials make consultation unnecessary.",
          "Consultation should occur only before a trial."
        ],
        "answer": 0,
        "evidence": "Such trials are not a substitute for consultation."
      },
      {
        "type": "true_false",
        "prompt": "Every business reported higher sales.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Other businesses saw little change."
      },
      {
        "type": "true_false",
        "prompt": "The council extended the trial to observe colder-weather use.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "It also extended the trial to observe how the space would be used in colder weather."
      },
      {
        "type": "choice",
        "prompt": "Why can average parking use hide important information?",
        "options": [
          "Demand can vary across different times",
          "Averages only describe pedestrian activity",
          "Parking spaces always have identical value"
        ],
        "answer": 0,
        "evidence": "Opponents were concerned that averages might conceal periods when parking was particularly valuable."
      },
      {
        "type": "choice",
        "prompt": "What helped the council evaluate the trial beyond comments?",
        "options": [
          "Removing all seating",
          "A permanent redesign",
          "Observations at different times of day"
        ],
        "answer": 2,
        "evidence": "It also recorded observations at different times of day rather than relying entirely on comments from the most frequent visitors."
      },
      {
        "type": "choice",
        "prompt": "Why might feedback collected only inside the square be biased?",
        "options": [
          "People who avoid the area are less likely to be represented",
          "The square has no visitors at any time",
          "All residents attend every public meeting"
        ],
        "answer": 0,
        "evidence": "If the council relied mainly on feedback collected inside the square, it might receive a disproportionately positive account of the trial."
      },
      {
        "type": "true_false",
        "prompt": "A temporary design still needs to address accessibility and maintenance.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Although the design was temporary, the organisers still had to consider accessibility, safe movement through the area and arrangements for maintenance."
      },
      {
        "type": "true_false",
        "prompt": "A successful trial in one location proves the same layout will work everywhere.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "A successful square in one location would provide evidence that a particular approach can work under certain conditions, not proof that every underused car park should be converted."
      }
    ]
  },
  {
    "id": "b2-05",
    "level": "B2",
    "title": "Reading the headlines critically",
    "titleUk": "Критичне читання заголовків",
    "paragraphs": [
      "Headlines are designed to attract attention, but the most noticeable sentence in an article is not always the most informative one. A headline may describe a small study as a major breakthrough, even when the researchers themselves are cautious about what their findings mean. This does not automatically make the article dishonest; space is limited and editors must decide which aspect of a story to emphasise. Nevertheless, readers should be aware of the difference between an attention-grabbing claim and the evidence that supports it.",
      "A useful habit is to identify the original source of a claim and examine its limitations. If a report describes an association between two behaviours, for example, it does not necessarily establish that one causes the other. Other factors may explain the relationship. Readers can also compare coverage from sources that provide independent reporting rather than simply repeating the same press release.",
      "Critical reading does not require rejecting everything that appears in the news. It involves adjusting confidence to match the strength of the evidence. Being willing to change an opinion when better information becomes available is a sign of careful judgment, not indecision.",
      "Suppose a reader encounters a headline claiming that a particular morning routine improves concentration. The article refers to a study in which people who followed the routine performed better on a short attention test. Before accepting the headline's interpretation, the reader would benefit from finding out how the participants were selected and whether the researchers assigned the routine to them. If participants chose their own routines, people who followed the recommended habit might already differ from those who did not. Such differences could influence the result independently of the routine itself.",
      "The distinction between a reported observation and an explanation for it is fundamental. Evidence of an association can provide a reasonable basis for further investigation. It does not, on its own, establish the direction of a causal relationship or rule out alternative explanations. The size of a study, the methods used and the conditions under which it was conducted can all affect the confidence with which its results should be interpreted. A finding may be interesting without being strong enough to justify a general recommendation.",
      "Headlines often omit these qualifications because they are designed to communicate a central idea in a small amount of space. A careful reader should therefore examine whether the body of an article supports the impression created by its title. Sometimes the article itself explains the uncertainty accurately. In other cases, important limitations are mentioned only briefly or not at all. The omission does not prove that a journalist intended to mislead, but it can still leave readers with a stronger conclusion than the available evidence supports.",
      "Comparing several articles can be useful, provided that the sources are genuinely independent. If five websites reproduce the same press release, their agreement does not constitute five separate investigations. Looking for reporting that consults the original research, asks additional experts for comments or examines alternative explanations can provide a wider perspective. It is also worth checking whether the headline describes a new finding or simply presents older information in a different context. Publication dates and links to original material help establish this distinction.",
      "Critical reading should not become a search for reasons to dismiss information that challenges an existing opinion. Readers can be equally demanding of claims they find attractive and claims they find disappointing. One practical habit is to separate what is directly supported from what remains uncertain. A person might accept that a study found a relationship in its participants while withholding judgment about whether the result applies to everyone. This is not the same as refusing to learn from the research. It is an attempt to make the strength of a belief proportionate to the strength of its support.",
      "In everyday life, there is rarely enough time to investigate every headline in detail. Readers can prioritise claims that would influence important decisions or that seem unusually surprising. They can examine the source before sharing such claims with others and avoid presenting a possibility as a certainty. When stronger evidence becomes available, they should be prepared to revise their interpretation. A thoughtful approach to news therefore combines curiosity with restraint. It treats headlines as invitations to investigate rather than as substitutes for the evidence that a reliable conclusion requires.",
      "The way a numerical result is presented can also influence the impression a headline creates. Suppose an article reports that a particular activity is associated with a reduction in the likelihood of an undesirable outcome. Describing a change as a percentage may sound dramatic, especially when the article does not explain the original level of risk. In a hypothetical example, a decrease from two cases in a hundred to one case in a hundred represents a reduction of one percentage point, or a relative reduction of fifty percent. Both descriptions are mathematically consistent, but they communicate different aspects of the result. A reader who sees only the relative percentage may form a different impression from someone who also knows the absolute numbers.",
      "Context is therefore important even when the figures in a headline are technically accurate. The number of participants, the length of the observation period and the population being studied can affect how useful the result is for a particular reader. An outcome observed in a small group over a short period may not necessarily occur in a larger or more diverse population. Similarly, a result obtained under carefully controlled conditions may differ from what happens in ordinary circumstances. These limitations do not mean that the research has no value. They indicate that its conclusions should be interpreted in relation to what was actually investigated.",
      "A separate issue concerns the selection of outcomes that are reported. A study may examine several different measures, only some of which show a noticeable change. A headline might focus on the most striking result while omitting other findings that make the overall picture more complicated. The reported result could be genuine, but a reader would need more information to understand whether it was the primary outcome the researchers intended to examine or one of several additional observations. Looking at the original research, when it is accessible, can help clarify the purpose of the study and the importance of the particular result highlighted in the article.",
      "The language used to describe uncertainty is another source of misunderstanding. Researchers may write that an explanation is consistent with their findings or that a particular relationship deserves further investigation. A headline may express the same idea in more definite language, describing the explanation as established. The change may seem small, but it alters the level of confidence communicated to the reader. Words such as 'may', 'suggests' and 'is associated with' can indicate meaningful differences between a possible interpretation and a conclusion supported by stronger evidence. Readers should pay attention to these distinctions rather than treat cautious language as an unnecessary weakness in a report.",
      "In some cases, the headline may be based on a statement from an organisation that has an interest in how the information is received. A company announcing a new product, for instance, may choose to emphasise findings that reflect well on it. An organisation advocating for a particular policy may highlight evidence that supports its proposal. These interests do not automatically invalidate the information, and a source with a clear position can still provide accurate evidence. Nevertheless, it is useful to identify who produced the information, how it was obtained and whether independent sources have examined it. Understanding a source's incentives helps readers decide what further verification would be appropriate.",
      "The speed at which information spreads online makes these questions particularly relevant. People often encounter a headline through a short message or a social media post rather than by visiting the original article. The surrounding comments may encourage a strong reaction before the reader has considered the evidence. Sharing a headline can feel like a quick way to inform others about something important, but it can also spread an interpretation that the underlying article does not support. Taking a moment to examine the source before sharing a surprising claim can reduce this risk. When the evidence is incomplete, describing the claim as uncertain is more accurate than presenting it as a settled fact.",
      "Critical readers should also examine their own reactions. Information that confirms an existing belief may appear more convincing because it fits with ideas the reader already accepts. Information that challenges that belief may receive greater scrutiny. This difference is understandable, but it can lead to inconsistent standards of evidence. A useful approach is to ask what kind of evidence would be required if the same claim supported the opposite position. If the standard changes substantially depending on whether the conclusion is welcome, the reader may be evaluating the claim partly according to preference rather than the quality of its support.",
      "Consider two articles that report apparently conflicting findings about the same subject. It may be tempting to conclude that one of them must be wrong. However, the studies they describe might have examined different populations, used different definitions or measured outcomes over different periods. Both findings could be accurate within their respective conditions. Before choosing between them, the reader should identify exactly what each claim refers to. Clarifying the apparent disagreement can sometimes reveal that the studies are addressing related but distinct questions. When the results do genuinely conflict, the next step is to consider the relative strength of the evidence rather than select the report with the most confident language.",
      "There are practical limits to how much investigation an ordinary reader can undertake. Research articles may be difficult to access or contain methods that require specialist knowledge. A reader who cannot fully evaluate a study can still make sensible distinctions between levels of confidence. They can look for reliable explanations from people with relevant expertise, check whether the conclusion is widely supported by independent work and avoid making important decisions on the basis of a single dramatic report. Recognising the limits of one's understanding is not a reason to accept every claim uncritically. It is a reason to seek appropriate support and express uncertainty when it remains.",
      "A well-informed opinion can change as evidence accumulates. Early findings may be revised when researchers conduct larger studies or examine alternative explanations. A claim that seemed plausible at one stage may receive less support later, while an initially uncertain result may become more credible through repeated investigation. Changing one's interpretation in response to these developments is a normal part of reasoning with incomplete information. It differs from changing opinions simply because a new headline is more dramatic than the previous one. The aim of critical reading is to establish a connection between confidence and evidence that remains open to revision. By approaching headlines as summaries that require context rather than final conclusions, readers can become more careful both in forming their own beliefs and in communicating information to others."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What distinction is central to the passage?",
        "options": [
          "Long articles versus short articles",
          "A striking claim versus the evidence supporting it",
          "Print journalism versus online journalism"
        ],
        "answer": 1,
        "evidence": "The difference between an attention-grabbing claim and the evidence that supports it."
      },
      {
        "type": "true_false",
        "prompt": "Independent reporting can help readers compare coverage.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "Readers can also compare coverage from sources that provide independent reporting."
      },
      {
        "type": "choice",
        "prompt": "Why does the author discuss associations?",
        "options": [
          "To show that a relationship does not automatically prove causation",
          "To claim that researchers cannot study behaviour",
          "To suggest all studies are unreliable"
        ],
        "answer": 0,
        "evidence": "It does not necessarily establish that one causes the other."
      },
      {
        "type": "choice",
        "prompt": "What attitude does the author encourage?",
        "options": [
          "Reject all news stories immediately.",
          "Keep an opinion regardless of new information.",
          "Adjust confidence when evidence changes."
        ],
        "answer": 2,
        "evidence": "Being willing to change an opinion when better information becomes available is a sign of careful judgment."
      },
      {
        "type": "true_false",
        "prompt": "The author says every exaggerated headline is deliberately dishonest.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "This does not automatically make the article dishonest."
      },
      {
        "type": "choice",
        "prompt": "Why does it matter whether study participants chose their own morning routines?",
        "options": [
          "Self-selection guarantees a causal result",
          "The headline is automatically true",
          "The groups may already have differed"
        ],
        "answer": 2,
        "evidence": "If participants chose their own routines, people who followed the recommended habit might already differ from those who did not."
      },
      {
        "type": "choice",
        "prompt": "What makes agreement between articles more informative?",
        "options": [
          "Identical wording from a press release",
          "Genuinely independent investigation",
          "More dramatic headlines"
        ],
        "answer": 1,
        "evidence": "Comparing several articles can be useful, provided that the sources are genuinely independent."
      },
      {
        "type": "choice",
        "prompt": "What is the absolute change from two cases in a hundred to one in a hundred?",
        "options": [
          "One percentage point",
          "Two percentage points",
          "Fifty percentage points"
        ],
        "answer": 0,
        "evidence": "In a hypothetical example, a decrease from two cases in a hundred to one case in a hundred represents a reduction of one percentage point, or a relative reduction of fifty percent."
      },
      {
        "type": "true_false",
        "prompt": "A study's finding can be interesting without justifying a general recommendation.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "A finding may be interesting without being strong enough to justify a general recommendation."
      },
      {
        "type": "true_false",
        "prompt": "Apparently conflicting studies must always contain an incorrect finding.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "Both findings could be accurate within their respective conditions."
      }
    ]
  },
  {
    "id": "b2-06",
    "level": "B2",
    "title": "Learning to disagree well",
    "titleUk": "Як конструктивно не погоджуватися",
    "paragraphs": [
      "In a discussion about a proposed school policy, two students presented opposing views. One argued that allowing phones during breaks would give students a welcome opportunity to relax. The other worried that constant access to screens might reduce face-to-face interaction. Initially, both treated the other’s concern as an obstacle to winning the debate. A teacher asked each student to explain the opposing argument in a way that the other would recognise as fair.",
      "This simple exercise changed the tone of the discussion. The students discovered that they shared a broader goal: making breaks enjoyable and restorative. They disagreed mainly about the best way to achieve it. Once this became clear, they began exploring alternatives, including optional phone-free areas, rather than repeating their original positions. They did not reach complete agreement, but they produced a proposal that addressed several concerns on both sides.",
      "Constructive disagreement does not require abandoning strongly held views. It requires distinguishing between a person and their argument, listening for common objectives, and being prepared to revise a proposal when a reasonable objection exposes a weakness. The outcome may be imperfect, but it is often more useful than a victory achieved by ignoring the other side.",
      "The students' initial disagreement was partly a result of the way the question had been framed. They had been asked whether phones should be permitted during breaks, which encouraged them to choose one of two opposing positions. A student who valued access to messages naturally focused on the advantages of permission, while someone concerned about social interaction focused on the advantages of restrictions. Both students gathered examples that supported their position, but neither spent much time considering the situations in which the other student's concern might be justified.",
      "The teacher's request to describe the opposing argument introduced a different task. Rather than prepare another response, each student had to listen for the reasons behind the other person's view. The student supporting access to phones discovered that the other was not primarily interested in controlling classmates. She was concerned that some students felt excluded when groups gathered around screens. The student supporting restrictions learned that his opponent valued the ability to contact family members and sometimes preferred a quiet break rather than continuous conversation.",
      "Presenting these concerns accurately did not require either student to agree with them. In fact, distinguishing understanding from agreement was essential to the exercise. People can acknowledge that a concern is reasonable while continuing to disagree about the most effective response. Once the students recognised this distinction, they became less defensive about their original positions. They could discuss what a proposal was intended to achieve instead of treating every criticism as a personal attack.",
      "The next stage was to explore alternative arrangements. An optional phone-free space might provide an opportunity for students who wanted conversation without preventing others from checking messages elsewhere. Clear exceptions could be considered for students who needed to contact someone. A short trial could help the school discover whether the arrangement was practical. These ideas did not eliminate every objection. Some students might still disagree about where the boundaries should be or how the policy would be applied. Nevertheless, considering alternatives broadened the discussion beyond a choice between complete permission and complete restriction.",
      "The teacher also encouraged the students to identify questions that could be answered through evidence. They could ask classmates how they preferred to spend breaks, observe whether existing spaces were being used and discuss practical concerns with the people responsible for supervision. Such information would not settle every question of principle, but it could reduce disagreement about the current situation. It would also help the students recognise when their assumptions were based mainly on their own experiences rather than those of the wider school community.",
      "Constructive disagreement has limits. Not every conflict can be resolved through a shared objective, and participants may have genuinely incompatible preferences. A useful discussion does not require everyone to compromise on every issue. It does require enough clarity to identify where disagreement remains and why. In this case, the students were able to produce a more detailed proposal because they listened to the concerns behind the opposing positions and considered additional possibilities. The process did not guarantee a perfect solution, but it made their arguments more precise and their proposal easier for others to evaluate. The ability to disagree well is therefore not a form of politeness alone. It is a practical way to improve decisions in situations where several legitimate needs must be considered.",
      "One reason disagreement can become unproductive is that participants sometimes defend a particular solution before establishing what problem they are attempting to solve. In the school debate, the question about phones had encouraged students to identify themselves with one of two positions. Once they had publicly supported a position, changing it could feel like admitting that they had been wrong. This emotional cost can make people reluctant to consider alternatives even when new information becomes available. Reframing the discussion around the purpose of school breaks helped the students separate their broader objectives from the particular rules they had initially proposed.",
      "The exercise of describing an opposing view also helped reveal the difference between a person's reasons and the consequences that another person attributes to their proposal. A student who supports restrictions on phone use might be accused of wanting to control everyone, although the actual concern is that some classmates feel excluded. A student who supports access to phones might be described as uninterested in social interaction, although they may simply value the freedom to choose how to spend a short break. These descriptions of motives can make disagreement more personal than necessary. Asking someone to explain their own reasons provides an opportunity to correct such assumptions before they become obstacles to further discussion.",
      "However, an accurate description of another view should not be confused with an obligation to accept every argument as equally strong. Some claims may be based on incomplete information or contain assumptions that can be challenged. A constructive discussion can examine those weaknesses directly without treating the person who made the argument as an enemy. For instance, if someone claims that all students prefer to spend their breaks using phones, the group can ask how that conclusion was reached and whether it represents the experiences of students who are less visible in the discussion. The aim is to identify what the claim actually establishes rather than dismiss it simply because it supports an opposing position.",
      "In the next stage of the school project, the students considered how the proposed phone-free area might affect different groups. A quiet area could be valuable to students who wanted to read, rest or talk without screens. Yet some students might need access to a device for reasons that were not immediately obvious to others. The students recognised that rules would need to be explained clearly and that appropriate exceptions would have to be considered by the school. They also discussed whether an optional area would remain useful if it became very crowded or if students felt pressured to use it. These practical questions helped them evaluate the alternative instead of assuming that a compromise was automatically a good solution.",
      "There is an important distinction between a compromise that addresses the underlying needs of different participants and one that simply divides the difference between their original demands. A rule allowing phones for half of every break might appear to provide equal concessions. However, it would not necessarily create a reliably screen-free environment for people who wanted one, and it might restrict access at inconvenient moments for others. An arrangement that provides different spaces or clearly defined options could address the concerns more directly. This does not prove that such an arrangement would work in every school. It demonstrates why examining the reasons behind competing proposals can lead to alternatives that are not obvious when people focus only on their initial positions.",
      "Evidence can help improve such a discussion, but participants should distinguish factual questions from judgments about what ought to happen. A survey might reveal how many students prefer particular activities during breaks. Observations might indicate whether a quiet space is currently available or whether some areas become overcrowded. This information could help the school assess practical options. Nevertheless, the final decision may still require judgments about how different needs should be balanced. A majority preference does not automatically resolve every concern, particularly when a smaller group has a significant need that others do not share. Evidence can clarify the situation without removing the need for reasonable judgment.",
      "The students therefore prepared a short proposal that identified the objectives, the possible arrangement and the questions that remained unanswered. Instead of stating that the proposal would solve every problem, they explained how it could be tested and what kinds of feedback would be useful. They also recorded the points on which they continued to disagree. This made their work more transparent to the teacher and to other students who had not participated in the original discussion. People could see how the proposal had developed and decide whether it addressed their own concerns. The written record helped prevent the students from presenting an incomplete agreement as if it were a unanimous decision.",
      "A similar approach can be useful in other situations. Imagine a group planning a shared study room. One member wants complete silence, while another prefers to work through difficult material by discussing it with a partner. If they frame the question as whether talking should be permitted, they may spend a long time arguing about a single rule. If they first consider why each person uses the room, they may discover that separate times or areas could meet both needs more effectively. The possibility of such an arrangement depends on the available space and the number of people involved. Understanding the different purposes of the room does not guarantee a solution, but it helps the group identify realistic options.",
      "Constructive disagreement also requires attention to the way a discussion is managed. People need a reasonable opportunity to explain their concerns, and important questions should not be ignored simply because one person speaks more confidently than another. At the same time, a discussion cannot continue indefinitely if a decision is needed. Participants can agree on the issues that require further information, establish when a decision must be made and identify who has responsibility for making it. A fair process may not produce the outcome that every person prefers, but it can help them understand the reasons for the decision and the extent to which their concerns were considered.",
      "Finally, disagreement can reveal that a proposal has strengths and weaknesses that were not visible when it was first introduced. An objection may identify a practical problem, while a question from someone with a different experience may suggest a useful improvement. Participants who regard every objection as a threat are more likely to miss these opportunities. Those who are prepared to examine objections can retain their important commitments while modifying the parts of a proposal that are less effective. The school students did not need to become identical in their preferences or abandon the concerns that had led them to disagree. They needed to develop a clearer understanding of the problem and of the consequences of possible decisions. In this sense, the ability to disagree constructively is not merely a social skill. It is a way of combining different forms of knowledge, recognising limitations and producing decisions that are more responsive to the circumstances in which they will be applied."
    ],
    "questions": [
      {
        "type": "choice",
        "prompt": "What did the teacher ask the students to do?",
        "options": [
          "Represent each other’s arguments fairly.",
          "Vote immediately on the policy.",
          "Stop expressing opposing views."
        ],
        "answer": 0,
        "evidence": "A teacher asked each student to explain the opposing argument in a way that the other would recognise as fair."
      },
      {
        "type": "choice",
        "prompt": "What common objective did they find?",
        "options": [
          "Removing all phones from the school",
          "Winning the debate quickly",
          "Making breaks enjoyable and restorative"
        ],
        "answer": 2,
        "evidence": "They shared a broader goal: making breaks enjoyable and restorative."
      },
      {
        "type": "choice",
        "prompt": "What is the author’s conclusion?",
        "options": [
          "Agreement is necessary for any useful outcome.",
          "Disagreement can be useful when objections improve proposals.",
          "Strong views must be abandoned to cooperate."
        ],
        "answer": 1,
        "evidence": "Being prepared to revise a proposal when a reasonable objection exposes a weakness."
      },
      {
        "type": "true_false",
        "prompt": "The students reached complete agreement.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "They did not reach complete agreement."
      },
      {
        "type": "true_false",
        "prompt": "The students explored optional phone-free areas.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "They began exploring alternatives, including optional phone-free areas."
      },
      {
        "type": "choice",
        "prompt": "What was one concern of the student supporting restrictions?",
        "options": [
          "All students disliked quiet breaks",
          "Some students felt excluded around screens",
          "Nobody should ever contact family"
        ],
        "answer": 1,
        "evidence": "She was concerned that some students felt excluded when groups gathered around screens."
      },
      {
        "type": "choice",
        "prompt": "What did the exercise demonstrate about understanding and agreement?",
        "options": [
          "Understanding does not require agreement",
          "Agreement makes listening unnecessary",
          "They are always identical"
        ],
        "answer": 0,
        "evidence": "Presenting these concerns accurately did not require either student to agree with them."
      },
      {
        "type": "choice",
        "prompt": "Why might simply allowing phones for half of every break be an unsuitable compromise?",
        "options": [
          "It completely removes the need for access exceptions",
          "It may not address the reasons behind either group's needs",
          "It necessarily provides a permanent quiet environment"
        ],
        "answer": 1,
        "evidence": "However, it would not necessarily create a reliably screen-free environment for people who wanted one, and it might restrict access at inconvenient moments for others."
      },
      {
        "type": "true_false",
        "prompt": "An optional phone-free space is discussed as one possible alternative.",
        "options": [
          "True",
          "False"
        ],
        "answer": 0,
        "evidence": "An optional phone-free space might provide an opportunity for students who wanted conversation without preventing others from checking messages elsewhere."
      },
      {
        "type": "true_false",
        "prompt": "The students present their remaining disagreements as if every participant agreed.",
        "options": [
          "True",
          "False"
        ],
        "answer": 1,
        "evidence": "The written record helped prevent the students from presenting an incomplete agreement as if it were a unanimous decision."
      }
    ]
  }
];
