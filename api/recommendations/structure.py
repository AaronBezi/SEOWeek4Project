# from pydantic import BaseModel, Field  #This allows us to get correctly formatted json responses back

# class BookSearchQueriesResponse(BaseModel):
#     queries: list[str] = Field(
#         min_length=1,
#         max_length=5,
#         description="Textbook search queries based on the study profile"
#     )

# # #structure for ranking books from books api   #no LONGER NEED NOT RETURNING SCORES ANYMORE TOO MUCH TIME
# # class RankedBook(BaseModel):
# #     book_id: str
# #     score: int = Field(ge=0,le=100)

# class BookRankingResponse(BaseModel):
#     recommendations: list[str] = Field(
#         min_length=1,
#         max_length=5,
#         description="The IDs of the five best matching books.")




#classes to provide structure for the recommendation responses