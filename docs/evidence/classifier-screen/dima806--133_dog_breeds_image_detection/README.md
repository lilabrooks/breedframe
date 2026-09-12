---
license: apache-2.0
metrics:
- accuracy
- f1
base_model:
- google/vit-base-patch16-224-in21k
---
Returns dog breed given an image.

See https://www.kaggle.com/code/dima806/133-dog-breed-image-detection-vit for more details.

![image/png](https://cdn-uploads.huggingface.co/production/uploads/6449300e3adf50d864095b90/9oA9yV4Rnd5p1zIQgcPbG.png)

```
Classification report:

                                    precision    recall  f1-score   support

                   Norwich_terrier     0.8750    0.8974    0.8861        39
                      Bichon_frise     0.8125    1.0000    0.8966        39
          Entlebucher_mountain_dog     0.8889    0.6316    0.7385        38
                            Briard     1.0000    1.0000    1.0000        39
                Norwegian_elkhound     0.9487    0.9487    0.9487        39
                     Field_spaniel     0.6731    0.9211    0.7778        38
                     Gordon_setter     0.9500    1.0000    0.9744        38
                    Cocker_spaniel     0.8378    0.8158    0.8267        38
                      Irish_setter     1.0000    0.9231    0.9600        39
       Wirehaired_pointing_griffon     0.7600    0.9744    0.8539        39
                   Giant_schnauzer     1.0000    0.9737    0.9867        38
                           Maltese     0.7755    1.0000    0.8736        38
          English_springer_spaniel     0.8571    0.9474    0.9000        38
              Bernese_mountain_dog     1.0000    0.9231    0.9600        39
                  Alaskan_malamute     1.0000    1.0000    1.0000        38
               American_eskimo_dog     0.9500    1.0000    0.9744        38
                          Havanese     0.0000    0.0000    0.0000        38
                Icelandic_sheepdog     0.9412    0.8421    0.8889        38
                Manchester_terrier     0.8298    1.0000    0.9070        39
                 Dogue_de_bordeaux     0.9048    0.9744    0.9383        39
              Cardigan_welsh_corgi     0.9231    0.6154    0.7385        39
                   Norfolk_terrier     0.9487    0.9487    0.9487        39
                        Canaan_dog     0.8800    0.5789    0.6984        38
                   Clumber_spaniel     0.9737    0.9737    0.9737        38
             Black_russian_terrier     0.9286    1.0000    0.9630        39
               German_shepherd_dog     0.8780    0.9474    0.9114        38
                     Affenpinscher     0.8837    0.9744    0.9268        39
                    Bearded_collie     0.9697    0.8421    0.9014        38
                  Chinese_shar-pei     0.9677    0.7692    0.8571        39
                Labrador_retriever     0.9333    0.3684    0.5283        38
                     Irish_terrier     0.9714    0.8947    0.9315        38
                   Chinese_crested     1.0000    0.8421    0.9143        38
            Anatolian_shepherd_dog     1.0000    0.8947    0.9444        38
                          Brittany     1.0000    0.8947    0.9444        38
                  Norwegian_buhund     0.8372    0.9474    0.8889        38
               Miniature_schnauzer     0.9512    1.0000    0.9750        39
                    Xoloitzcuintli     0.9750    1.0000    0.9873        39
                         Dalmatian     0.8667    1.0000    0.9286        39
                         Greyhound     0.8750    0.9211    0.8974        38
                        Leonberger     1.0000    1.0000    1.0000        39
                      Ibizan_hound     1.0000    0.9487    0.9737        39
                        Bloodhound     1.0000    1.0000    1.0000        38
                Bluetick_coonhound     1.0000    1.0000    1.0000        39
                    English_setter     1.0000    1.0000    1.0000        38
                Neapolitan_mastiff     0.8864    1.0000    0.9398        39
            Parson_russell_terrier     0.9167    0.8462    0.8800        39
                  Brussels_griffon     0.9714    0.8947    0.9315        38
                           Bulldog     0.9268    1.0000    0.9620        38
                       Bullmastiff     0.7857    0.5641    0.6567        39
                            Borzoi     1.0000    1.0000    1.0000        38
                            Poodle     1.0000    0.8421    0.9143        38
                            Kuvasz     0.8500    0.8947    0.8718        38
                             Plott     0.8810    0.9737    0.9250        38
                  Belgian_malinois     0.9722    0.9211    0.9459        38
                     Japanese_chin     0.9286    1.0000    0.9630        39
                Smooth_fox_terrier     0.9024    0.9737    0.9367        38
             Flat-coated_retriever     0.8298    1.0000    0.9070        39
                           Pointer     1.0000    0.6316    0.7742        38
                        Otterhound     0.9487    0.9737    0.9610        38
                        Pomeranian     0.9167    0.8684    0.8919        38
                        Lhasa_apso     0.8444    0.9744    0.9048        39
              Bouvier_des_flandres     0.9737    0.9737    0.9737        38
               Irish_water_spaniel     0.9730    0.9474    0.9600        38
              Old_english_sheepdog     0.8837    0.9744    0.9268        39
                      Basset_hound     1.0000    0.9744    0.9870        39
            American_water_spaniel     0.8571    0.9474    0.9000        38
                  Airedale_terrier     0.7308    1.0000    0.8444        38
                    Border_terrier     0.9730    0.9474    0.9600        38
                   Irish_wolfhound     1.0000    1.0000    1.0000        39
                 Yorkshire_terrier     0.7037    1.0000    0.8261        38
                          Papillon     0.9048    1.0000    0.9500        38
                         Dachshund     1.0000    0.7895    0.8824        38
     Cavalier_king_charles_spaniel     0.8140    0.9211    0.8642        38
                   Tibetan_mastiff     1.0000    0.9487    0.9737        39
                         Pekingese     1.0000    0.9211    0.9589        38
         German_wirehaired_pointer     1.0000    0.6316    0.7742        38
                 Doberman_pinscher     0.6102    0.9474    0.7423        38
                          Keeshond     1.0000    1.0000    1.0000        39
            Dandie_dinmont_terrier     1.0000    0.9737    0.9867        38
    American_staffordshire_terrier     0.8718    0.8947    0.8831        38
                     Cairn_terrier     1.0000    0.9744    0.9870        39
              Portuguese_water_dog     0.9722    0.8974    0.9333        39
                  Golden_retriever     0.9000    0.9474    0.9231        38
                           Basenji     0.8125    1.0000    0.8966        39
                Bedlington_terrier     1.0000    0.9737    0.9867        38
                      Newfoundland     0.9737    0.9737    0.9737        38
                             Boxer     0.8444    0.9744    0.9048        39
              Pembroke_welsh_corgi     0.6923    0.9474    0.8000        38
                   German_pinscher     1.0000    0.3846    0.5556        39
          Chesapeake_bay_retriever     1.0000    0.9474    0.9730        38
                         Chow_chow     1.0000    1.0000    1.0000        38
                            Collie     0.9500    1.0000    0.9744        38
                          Komondor     1.0000    1.0000    1.0000        38
                    Boston_terrier     1.0000    1.0000    1.0000        39
             Glen_of_imaal_terrier     0.9231    0.9231    0.9231        39
                         Beauceron     0.9429    0.8462    0.8919        39
                  Belgian_sheepdog     1.0000    1.0000    1.0000        38
                      Bull_terrier     1.0000    0.9737    0.9867        38
        German_shorthaired_pointer     0.7917    1.0000    0.8837        38
                     Silky_terrier     0.9545    0.5526    0.7000        38
                        Great_dane     0.9630    0.6667    0.7879        39
                    French_bulldog     1.0000    0.9474    0.9730        38
            Welsh_springer_spaniel     0.7600    1.0000    0.8636        38
            Curly-coated_retriever     0.8810    0.9487    0.9136        39
                        Cane_corso     0.8250    0.8462    0.8354        39
                 Italian_greyhound     0.8780    0.9231    0.9000        39
                Australian_terrier     0.9487    0.9487    0.9487        39
               Australian_shepherd     0.9722    0.9211    0.9459        38
                  Belgian_tervuren     0.9500    0.9744    0.9620        39
                  Lakeland_terrier     1.0000    0.5263    0.6897        38
                     Finnish_spitz     0.9000    0.9474    0.9231        38
               English_toy_spaniel     0.9375    0.7895    0.8571        38
                    Boykin_spaniel     0.8750    0.5526    0.6774        38
                     Pharaoh_hound     0.9024    0.9737    0.9367        38
                      Afghan_hound     0.9250    0.9487    0.9367        39
                 American_foxhound     0.9355    0.7436    0.8286        39
                           Lowchen     0.5965    0.8718    0.7083        39
                           Mastiff     0.7500    0.9474    0.8372        38
      Petit_basset_griffon_vendeen     0.9070    1.0000    0.9512        39
                Kerry_blue_terrier     0.8478    1.0000    0.9176        39
        Irish_red_and_white_setter     0.8919    0.8462    0.8684        39
             Australian_cattle_dog     1.0000    0.9474    0.9730        38
                            Beagle     0.7551    0.9737    0.8506        38
                    Great_pyrenees     0.7805    0.8421    0.8101        38
                     Border_collie     0.9744    1.0000    0.9870        38
                     Saint_bernard     1.0000    1.0000    1.0000        38
                             Akita     0.8182    0.7105    0.7606        38
               Norwegian_lundehund     0.8261    1.0000    0.9048        38
Nova_scotia_duck_tolling_retriever     0.9211    0.9211    0.9211        38
        Greater_swiss_mountain_dog     0.6667    0.9231    0.7742        39
                         Chihuahua     1.0000    0.9487    0.9737        39
           Black_and_tan_coonhound     0.8667    1.0000    0.9286        39
            English_cocker_spaniel     0.8710    0.7105    0.7826        38

                          accuracy                         0.9017      5108
                         macro avg     0.9061    0.9015    0.8955      5108
                      weighted avg     0.9061    0.9017    0.8957      5108
```