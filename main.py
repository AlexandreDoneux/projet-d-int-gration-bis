import sounddevice as sd
import numpy as np
import speech_recognition as sr
import boto3
import json
import aws



target_words_list = ["On mange", "Professeur"," Je ne comprends pas"]  
sound_limit = 100
aws_access_key_id = 'AKIA2LHQVF4P2MD7O4S6'
aws_secret_access_key = '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'
region_name = 'eu-west-3'
queue_url_get = 'https://sqs.eu-west-3.amazonaws.com/711321792287/integration_App_To_Rpi'    

sqs_client = boto3.client('sqs', region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)




def main():
    global sound_limit
    global target_words_list
    recognizer = sr.Recognizer()

    def print_sound(indata, outdata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10
        if volume_norm > sound_limit:
            print("c'est trop fort")        
            aws.send_message_to_sqs("SeuilMic","Trop fort")

    with sd.Stream(callback=print_sound):
        while True:    
            response = sqs_client.receive_message(
                QueueUrl=queue_url_get,
                MaxNumberOfMessages=1,
                MessageAttributeNames=['All'],
                AttributeNames=['SentTimestamp']
            ) 
            messages = response.get('Messages', [])
                
            if messages:
                message = messages[0]
                body = json.loads(message['Body'])
                new_message = body['Message']

                
                data_reçue = new_message
                print('Message reçu:', data_reçue)
                result_array = data_reçue.split(":")
                if "SeuilMic" in result_array:
                    sound_limit= result_array[1]
                    print( "nouveau seuil minimak : " + str(sound_limit))
                if "DétectionMsg" in result_array:
                    target_words_list.append(result_array[1])  
                    print(target_words_list)  
                    
                receipt_handle=message["ReceiptHandle"]
                print(receipt_handle)
                try :
                    print("message bien supprimé de la file")
                    sqs_client.delete_message(QueueUrl= queue_url_get, ReceiptHandle= receipt_handle)
                except Exception as exc:
                    print('Erreur de delete:' + str(exc))
                                    
            with sr.Microphone() as source:
                print("Dites quelque chose...")
                audio = recognizer.listen(source)

            try:
                text = recognizer.recognize_google(audio, language="fr-FR")
                print("Texte reconnu:", text)

                text_lower = text.lower()

                for word in target_words_list:
                    if word.lower() in text_lower:
                        print(f"Le mot '{word}' a été détecté dans l'audio.")
                        aws.send_message_to_sqs("DétectionMsg",word)

            except sr.UnknownValueError:
                print("Non reconnu")
            except sr.RequestError as e:
                print("Erreur lors de la demande au service Google : {0}".format(e))
                
        




if __name__ == "__main__":
    
    main()

