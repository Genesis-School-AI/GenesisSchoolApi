# TOTH API

The TOTH API is a FastAPI-based web application that provides a set of endpoints for interacting with a database and generating responses based on user input.

## Installation

To set up the TOTH API, follow these steps:

1. Clone the repository:
```
git clone https://github.com/Genesis-School-AI/GenesisSchoolApi.git
```

2. Navigate to the project directory:
```
cd GenesisSchoolApi
```

3. Install the required dependencies:
```
pip install -r ./setup/requirements.txt
```

4. Run the development server:
```
uvicorn toth_api:app --host 127.0.0.1 --port 8690 --reload
```

The API will be available at `http://127.0.0.1:8690`.

## Usage

The TOTH API provides two main endpoints:

### `POST /fetch-response`

This endpoint allows you to fetch a response from the database based on the provided parameters.

**Request Body**:
```json
{
    "k" : 5,
    "room_id" : 301,
    "year_id" : 3,
    "subject_id" : "bio",
    "prompt" : "เรียนอะไรบ้าง"
}
```

**Response**:
```json
{
    "message": [
        [
            0.2963753216080868,
            "the content ",
            "2025-06-27T00:00:00",
            6000.0,
            "อาจารย์วรเพียร์",
            "bio",
            3,
            301
        ]
    ],
    "k": 5,
    "data": "เรียนร่างกาย . . . **All respond"
}
```

### `POST /add-document`

This endpoint allows you to add a new document to the database.

**Request Body**:
```json
{
    "content": {
        "teacher_name": "ครูA",
        "teacher_subject": "math",
        "time_summit": "2025-07-04T09:00:00",   
        "time_of_record": "00:30:00",
        "student_year": 3,
        "student_room": 302,
        "content": "สวัสดีนักเรียนทุกคน สอง คูณ สาม ไม่เท่ากับ หก เป็นเท็จ วันนี้พอแค่นี้นะครับ"
    }
}
```

**Response**:
```json
{
    "message": {
        "teacher_name": "ครูA",
        "teacher_subject": "math",
        "time_summit": "2025-07-04T09:00:00",
        "time_of_record": "00:30:00",
        "student_year": 3,
        "student_room": 302,
        "content": "สวัสดีนักเรียนทุกคน สอง คูณ สาม ไม่เท่ากับ หก เป็นเท็จ วันนี้พอแค่นี้นะครับ"
    },
    "content": "Document added successfully"
}
```

## API

The TOTH API exposes the following endpoints:

- `GET /`: Returns a simple "Hello" message.
- `POST /fetch-response`: Fetches a response from the database based on the provided parameters.
- `POST /add-document`: Adds a new document to the database.

## Contributing

If you would like to contribute to the TOTH API, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your changes to your forked repository.
5. Submit a pull request to the main repository.

## License

This project is licensed under the [MIT License](LICENSE).
